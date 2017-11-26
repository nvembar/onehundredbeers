"""The validation views"""

import math
import logging
import json
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse, HttpResponseBadRequest
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from beers.models import Contest, Contest_Checkin, Contest_Beer, \
                         Contest_Player, Contest_Brewery, Unvalidated_Checkin
from .helper import is_authenticated_user_contest_runner, \
                    HttpNotImplementedResponse

logger = logging.getLogger(__name__)

class BadValidationResponse(BaseException):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

def align_contest_and_checkin(request, contest_id, uv_checkin):
    """Checks whether the user making the request is the owner of the
    contest, the checkin exists, and is part of the contest"""
    uv = get_object_or_404(Unvalidated_Checkin.objects.select_related(),
                           id=uv_checkin)
    contest = get_object_or_404(Contest.objects, id=contest_id)
    if uv.contest_player.contest.id != int(contest_id):
        logger.warning('Bad contest match: [%s] vs. [%s]',
                       uv.contest_player.contest.id, contest_id)
        raise BadValidationResponse('Checkin not associated with contest')
    if not is_authenticated_user_contest_runner(request):
        logger.warning('User %s attempted to validate checkins for contest %s',
                       request.user.username, contest_id)
        raise PermissionDenied("User is not allowed to validate checkins")
    if contest.creator.user.id is not request.user.id:
        logger.warning('User %s attempted to validate checkins ' +
                       'for contest "%s" that they do not own: should be %s',
                       request.user.username, contest.name,
                       contest.creator.user.username)
    return {'contest': contest, 'uv': uv}


@login_required
@require_http_methods(['POST'])
@transaction.atomic
def validate_checkin(request, contest_id):
    """
    Adds a checkin to a brewery via a POST (as it should do)

    POST expects a brewery to come in the form:
        { 'as_brewery': id, 
          'checkin': id, 
          'bonuses': [ <list of bonuses> ],
          'preserve': true/false }

    as_brewery: The contest brewery ID
    checkin: Unvalidated checkin ID
    bonuses: Optional tag with a list of bonus tags this checkin gets
    preserve: Whether to save the unvalidated checkin or not


    POST expects beer to come in the form:
        { 'as_beer': id, 
          'checkin': id, 
          'bonuses': [ <list of bonuses> ],
          'preserve': true/false }

    as_beer: The contest beer ID
    checkin: Unvalidated checkin ID
    bonuses: Optional tag with a list of bonus tags this checkin gets
    preserve: Whether to save the unvalidated checkin or not

    Additionally, if this is just a bonus checkin, both 'as_beer' and 'as_brewery'
    can be omitted.

    """
    values = None
    data = None
    uv_checkin = None
    try:
        data = json.loads(request.body)
        uv_checkin = int(data['checkin'])
    except KeyError:
        return HttpResponseBadRequest('Invalid request, expected checkin ID')
    except ValueError:
        return HttpResponseBadRequest('Invalid request, checkin ID should be '
                                      + 'an integer')
    except json.JSONDecodeError as exc:
        return HttpResponseBadRequest('Invalid request, not JSON: {}'
                                      .format(exc))
    try:
        values = align_contest_and_checkin(request, contest_id, uv_checkin)
    except BadValidationResponse as exc:
        return HttpResponseBadRequest(exc.value)
    uv = values['uv']
    contest = values['contest']
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError as exc:
        return HttpResponseBadRequest('Invalid request, not JSON: {}'
                                      .format(exc))
    checkin = None
    contest_player = uv.contest_player
    if 'as_brewery' in data:
        contest_brewery = None
        try:
            contest_brewery = Contest_Brewery.objects.get(
                id=data['as_brewery'])
        except Contest_Brewery.DoesNotExist:
            return HttpResponseBadRequest(
                'No such brewery with id {}'.format(data['as_brewery']))
        if contest_brewery.contest.id != contest.id:
            return HttpResponseBadRequest(
                'Brewery is not associated with contest')
        checkin = contest_player.drink_at_brewery(contest_brewery, uv)
    elif 'as_beer' in data:
        contest_beer = None
        try:
            contest_beer = Contest_Beer.objects.get(id=data['as_beer'])
        except Contest_Beer.DoesNotExist:
            return HttpResponseBadRequest(
                'No such beer with id {}'.format(data['as_beer']))
        if contest_beer.contest.id != contest.id:
            return HttpResponseBadRequest(
                'Beer is not associated with contest')
        checkin = contest_player.drink_beer(contest_beer, uv)
    if 'bonuses' in data:
        # for the moment, prefer the checkin for beers or breweries over
        # bonus checkins. Will need to fix this so it returns all relevant checkins
        for bonus in data['bonuses']:
            bonus_checkin = contest_player.drink_bonus(bonus, checkin=uv)
        if checkin is None:
            checkin = bonus_checkin
    if not data.get('preserve'):
        uv.delete()
    if request.META.get('HTTP_ACCEPT') == 'application/json':
        return HttpResponse(json.dumps({'success': True,
                                        'checkin_id': checkin.id}),
                            content_type='application/json')
    return redirect('unvalidated-checkins', contest_id)


@login_required
@require_http_methods(['DELETE'])
@transaction.atomic
def delete_checkin(request, contest_id, uv_checkin):
    """Deletes an unvalidated checkin"""
    values = None
    try:
        values = align_contest_and_checkin(request, contest_id, uv_checkin)
    except BadValidationResponse as exc:
        return HttpResponseBadRequest(exc.value)
    uv = values['uv']
    uv.delete()
    if request.META.get('HTTP_ACCEPT') == 'application/json':
        return HttpResponse('{ "success": true }',
                            content_type='application/json')
    return redirect('unvalidated-checkins', contest_id)


@login_required
@require_http_methods(['GET'])
def unvalidated_checkins_json(request, contest_id):
    """
    Provides a JSON object with all the checkins between the two slices
    slice_start is the first index to pull
    slice_end is the non-inclusive end index
    """
    contest = get_object_or_404(Contest.objects, id=contest_id)
    if not is_authenticated_user_contest_runner(request):
        logger.warning("User %s attempted to validate checkins for contest %s",
                       request.user.username, contest_id)
        raise PermissionDenied("User is not allowed to validate checkins")
    if contest.creator.user.id is not request.user.id:
        logger.warning("User %s attempted to validate checkins " +
                       "for contest '%s' that they do not own",
                       request.user.username, contest.name)
        raise PermissionDenied("User is not the contest runner")

    def get_integer_param(name, default=None):
        try:
            param = int(request.GET.get(name, default))
            if param is None:
                raise HttpResponseBadRequest(("Parameter '{}' must be an "
                                              + "integer").format(name))
            return param
        except KeyError:
            raise HttpResponseBadRequest("Request must include '{}'"
                                         .format(name))
    slice_start = get_integer_param('slice_start')
    slice_end = get_integer_param('slice_end')
    page_size = get_integer_param('page_size', 25)
    if slice_start >= slice_end:
        raise HttpResponseBadRequest("Slice start must be less than slice end")
    uvs = Unvalidated_Checkin.objects.filter(
        contest_player__contest_id=contest_id).order_by('untappd_checkin_date')
    page_count = math.ceil(uvs.count() / page_size)
    page_index = math.ceil(slice_start / page_size)
    beers = Contest_Beer.objects.filter(
        contest_id=contest_id).order_by('beer_name')

    def to_result(uv, i):
        """Maps a checkin to a response object"""
        result = {
            'id': uv.id,
            'index': i,
            'player': uv.contest_player.user_name,
            'checkin_url': uv.untappd_checkin,
            'beer': uv.beer,
            'brewery': uv.brewery,
            'checkin_date': uv.untappd_checkin_date.strftime('%m/%d/%Y'),
        }
        try:
            beer = beers.get(beer_name=uv.beer)
            result['possible_name'] = beer.beer_name
            result['possible_id'] = beer.id
        except Contest_Beer.DoesNotExist:
            pass
        return result
    result = {
        'page_count': page_count,
        'page_index': page_index,
        'page_size': page_size,
        'checkins': list(map(to_result,
                             uvs[slice_start:slice_end],
                             range(slice_start, slice_end))),
    }
    return HttpResponse(json.dumps(result, indent=True),
                        content_type='application/json')


@login_required
def unvalidated_checkins(request, contest_id):
    """Presents all the unvalidated checkins to the contest runner for
    approval"""
    contest = get_object_or_404(Contest.objects, id=contest_id)
    if not is_authenticated_user_contest_runner(request):
        logger.warning("User %s attempted to validate checkins for contest %s",
                       request.user.username, contest_id)
        raise PermissionDenied("User is not allowed to validate checkins")
    if contest.creator.user.id is not request.user.id:
        logger.warning("User %s attempted to validate checkins " +
                       "for contest '%s' that they do not own: should be %s",
                       request.user.username,
                       contest.name,
                       contest.creator.user.username)
        raise PermissionDenied("User is not the contest runner")
    uvs_all = Unvalidated_Checkin.objects.filter(
        contest_player__contest_id=contest_id).order_by('untappd_checkin_date')
    paginator = Paginator(uvs_all, 25)
    page = request.GET.get('page')
    try:
        uvs = paginator.page(page)
    except PageNotAnInteger:
        uvs = paginator.page(1)
    except EmptyPage:
        uvs = paginator.page(paginator.num_pages)
    beers = Contest_Beer.objects.filter(
        contest_id=contest_id).order_by('beer_name')
    breweries = Contest_Brewery.objects.filter(
        contest_id=contest_id).order_by('brewery_name')
    for uv in uvs:
        try:
            uv.possible_beer = beers.get(beer_name=uv.beer)
        except Contest_Beer.DoesNotExist:
            pass
        try:
            uv.possible_brewery = breweries.get(brewery_name=uv.brewery)
        except Contest_Brewery.DoesNotExist:
            pass
    context = {'uvs': uvs,
               'contest': contest,
               'beers': beers,
               'breweries': breweries,
              }
    return render(request, 'beers/validate.html', context)


@login_required
def initiate_recover(request, contest_id):
    contest = get_object_or_404(Contest.objects, id=contest_id)
    if not is_authenticated_user_contest_runner(request):
        logger.warning("User %s attempted to recover a checkin for contest %s",
                       request.user.username, contest_id)
        raise PermissionDenied("User is not allowed to recover checkins")
    if contest.creator.user.id is not request.user.id:
        logger.warning("User %s attempted to recover a checkin " +
                       "for contest '%s' that they do not own: should be %s",
                       request.user.username,
                       contest.name,
                       contest.creator.user.username)
        raise PermissionDenied("User is not the contest runner")
    context = {'contest': contest}
    return render(request, 'beers/initiate-recover.html', context)
