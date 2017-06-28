from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseServerError
from django.db import transaction
from django.db.models import Sum
from django.contrib.auth import authenticate
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist, MultipleObjectsReturned
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from beers.models import Contest, Beer, Player, Checkin, Contest_Checkin, Contest_Beer, Contest_Player, Contest_Brewery, Unvalidated_Checkin
from beers.utils.checkin import checkin_brewery
from .helper import is_authenticated_user_contest_runner, is_authenticated_user_player
from .helper import HttpNotImplementedResponse
import math
import logging
import json
import datetime

logger = logging.getLogger(__name__)

class BadValidationResponse(BaseException):
	def __init__(self, value):
		self.value = value

	def __str__(self):
		return repr(self.value)

def align_contest_and_checkin(request, contest_id, uv_checkin):
	uv = get_object_or_404(Unvalidated_Checkin.objects.select_related(), id=uv_checkin)
	contest = get_object_or_404(Contest.objects, id=contest_id)
	if uv.contest_player.contest.id != int(contest_id):
		logger.warning("Bad contest match: [{0}] vs. [{1}]".format(uv.contest_player.contest.id,contest_id))
		raise BadValidationResponse('Checkin not associated with contest')
	if not is_authenticated_user_contest_runner(request):
		logger.warning("User {0} attempted to validate checkins for contest {1}"
					.format(request.user.name, contest_id))
		raise PermissionDenied("User is not allowed to validate checkins")
	if not contest.creator.user.id is request.user.id:
		logger.warning("User {0} attempted to validate checkins " +
						"for contest '{1}' that they do not own: should be {2}"
					.format(request.user.username, contest.name,
					contest.creator.user.username))
	return { 'contest': contest, 'uv': uv }

@login_required
@require_http_methods(['POST'])
@transaction.atomic
def add_brewery_checkin(request, contest_id, uv_checkin):
	"""
	Adds a checkin to a brewery via a POST (like it should do)

	Expects data in the form { 'as_brewery': id, 'preserve': true/false }

	as_brewery: The contest brewery ID
	preserve: Whether to save the unvalidated checkin or not
	"""
	values = None
	try:
		values = align_contest_and_checkin(request, contest_id, uv_checkin)
	except BadValidationResponse as e:
		return HttpResponseBadRequest(e.value)
	uv = values['uv']
	contest = values['contest']
	data = None
	try:
		data = json.loads(request.body)
	except json.JSONDecoderError as e:
		return HttpResponseBadRequest('Invalid request, not JSON: {}'.format(e))
	contest_brewery = None
	try:
		contest_brewery = Contest_Brewery.objects.get(id=data['as_brewery'])
	except Contest_Brewery.DoesNotExist as e:
		return HttpResponseBadRequest(
			'No such brewery with id {}'.format(data['as_brewery']))
	checkin = checkin_brewery(uv, contest_brewery, save_checkin=data.get('preserve', False))
	if request.META.get('HTTP_ACCEPT') == 'application/json':
		return HttpResponse(
			json.dumps({ 'success': True, 'checkin_id': checkin.id, }),
			content_type='application/json',
			)
	else:
		return redirect('unvalidated-checkins', contest_id)

@login_required
@require_http_methods(['POST'])
@transaction.atomic
def update_checkin(request, contest_id, uv_checkin):
	# XXX: Refactor this into something more like add_brwery_checkin()
	values = None
	try:
		values = align_contest_and_checkin(request, contest_id, uv_checkin)
	except BadValidationResponse as e:
		return HttpResponseBadRequest(e.value)
	uv = values['uv']
	contest = values['contest']
	data = None
	try:
		data = json.loads(request.body)
	except json.JSONDecodeError as e:
		return HttpResponseBadRequest('Invalid request, not JSON: {}'.format(e))
	if data.get('remove-beer') == 'Remove':
		uv.delete();
		if request.META.get('HTTP_ACCEPT') == 'application/json':
			return HttpResponse('{ "success": true }', content_type='application/json')
		else:
			return redirect('unvalidated-checkins', contest_id)
	# This should be a validation, so it needs the validate beer value
	# and contest beer identifier
	contest_beer = None
	if not ('contest-beer' in data and data.get('validate-beer') == 'Validate'):
		return HttpResponseBadRequest('Invalid JSON: {}'.format(request.body))
	logger.info('Attempting to set UV {} to beer # {}'.format(uv.id, data['contest-beer']))
	try:
		contest_beer = Contest_Beer.objects.get(id=int(data['contest-beer']))
	except ValueError as e:
		return HttpResponseBadRequest('Invalid beer ID: {}'.format(data['contest-beer']))
	except ObjectDoesNotExist as e:
		return HttpResponseBadRequest(
			'No such beer with id {}'.format(data['contest-beer']))
	except MultipleObjectsReturned as e:
		logger.error('Multiple beers with the same ID: {}'.format(data['contest-beer']))
		return HttpResponseServerError('Database error')
	existing_cnt = Contest_Checkin.objects.filter(
			contest_player_id=uv.contest_player.id,
			contest_beer_id=contest_beer.id).count()
	# User hasn't checked into the beer before
	if existing_cnt == 0:
		checkin = Contest_Checkin.objects.create_checkin(
				contest_player=uv.contest_player,
				contest_beer=contest_beer,
				checkin_time=uv.untappd_checkin_date,
				untappd_checkin=uv.untappd_checkin)
		checkin.save()
		# We can do this incrementally, but will do it the bad way first before moving
		# this to the utility function
		uv.contest_player.compute_points()
		if (uv.contest_player.last_checkin_date is None or
				uv.untappd_checkin_date > uv.contest_player.last_checkin_date):
			uv.contest_player.last_checkin_date = uv.untappd_checkin_date
			uv.contest_player.last_checkin_beer = contest_beer.beer_name
		uv.contest_player.save()
	uv.delete() # clear the unvalidated checkin
	if request.META.get('HTTP_ACCEPT') == 'application/json':
		return HttpResponse('{ "success": true }', content_type='application/json')
	else:
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
		logger.warning("User {0} attempted to validate checkins for contest {1}"
					.format(request.user.username, contest_id))
		raise PermissionDenied("User is not allowed to validate checkins")
	if not contest.creator.user.id is request.user.id:
		logger.warning("User {0} attempted to validate checkins " +
						"for contest '{1}' that they do not own"
					.format(request.user.username, contest.name))
		raise PermissionDenied("User is not the contest runner")
	def get_integer_param(name, default=None):
		try:
			r = int(request.GET.get(name, default))
			if r is None:
				raise HttpResponseBadRequest("Parameter '{}' must be an integer".format(name))
			return r
		except KeyError as e:
			raise HttpResponseBadRequest("Request must include '{}'".format(name))
	slice_start = get_integer_param('slice_start')
	slice_end = get_integer_param('slice_end')
	page_size = get_integer_param('page_size', 25)
	if slice_start >= slice_end:
		raise HttpResponseBadRequest("Slice start must be less than slice end")
	uvs = Unvalidated_Checkin.objects.filter(
			contest_player__contest_id=contest_id).order_by('untappd_checkin_date')
	page_count = math.ceil(uvs.count() / page_size)
	page_index = math.ceil(slice_start / page_size)
	beers = Contest_Beer.objects.filter(contest_id=contest_id).order_by('beer_name')
	def to_result(uv, i):
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
			b = beers.get(beer_name=uv.beer)
			result['possible_name'] = b.beer_name
			result['possible_id'] = b.id
		except:
			pass
		return result
	result = {
		'page_count': page_count,
		'page_index': page_index,
		'page_size': page_size,
		'checkins': list(map(to_result, uvs[slice_start:slice_end], range(slice_start,slice_end))),
	}
	return HttpResponse(json.dumps(result, indent=True), content_type='application/json')

@login_required
def unvalidated_checkins(request, contest_id):
	"""Presents all the unvalidated checkins to the contest runner for approval"""
	contest = get_object_or_404(Contest.objects, id=contest_id)
	if not is_authenticated_user_contest_runner(request):
		logger.warning("User {0} attempted to validate checkins for contest {1}"
					.format(request.user.username, contest_id))
		raise PermissionDenied("User is not allowed to validate checkins")
	if not contest.creator.user.id is request.user.id:
		logger.warning("User {0} attempted to validate checkins " +
						"for contest '{1}' that they do not own: should be {2}"
					.format(request.user.username, contest.name,
					contest.creator.user.username))
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
	beers = Contest_Beer.objects.filter(contest_id=contest_id).order_by('beer_name')
	breweries = Contest_Brewery.objects.filter(contest_id=contest_id).order_by('brewery_name')
	for uv in uvs:
		try:
			uv.possible_beer = beers.get(beer_name=uv.beer)
		except Contest_Beer.DoesNotExist:
			pass
		try:
			uv.possible_brewery  = breweries.get(brewery_name=uv.brewery)
		except Contest_Brewery.DoesNotExist:
			pass
	context = { 'uvs': uvs, 'contest': contest, 'beers': beers, 'breweries': breweries, }
	return render(request, 'beers/validate.html', context)

@login_required
def initiate_recover(request, contest_id):
	contest = get_object_or_404(Contest.objects, id=contest_id)
	if not is_authenticated_user_contest_runner(request):
		logger.warning("User {0} attempted to recover a chekcin for contest {1}"
					.format(request.user.username, contest_id))
		raise PermissionDenied("User is not allowed to recover checkins")
	if not contest.creator.user.id is request.user.id:
		logger.warning("User {0} attempted to recover a checkin " +
						"for contest '{1}' that they do not own: should be {2}"
					.format(request.user.username, contest.name,
					contest.creator.user.username))
		raise PermissionDenied("User is not the contest runner")
	context = { 'contest': contest }
	return render(request, 'beers/initiate-recover.html', context)
