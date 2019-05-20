import logging
from beers.models import Unvalidated_Checkin, Contest, Contest_Player
from beers.utils.untappd import parse_checkin, UntappdParseException
from .helper import is_authenticated_user_contest_runner
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse, HttpResponseBadRequest
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_http_methods

logger = logging.getLogger(__name__)

@login_required
@require_http_methods(['POST'])
def add_unvalidated_checkin(request, contest_id):
    """
    Adds an unvalidated checkin by its Untappd URL
    """
    contest = get_object_or_404(Contest, id=contest_id)
    if not is_authenticated_user_contest_runner(request):
        logger.warning("User %s attempted to validate checkins for contest %s",
                       request.user.username, contest_id)
        raise PermissionDenied("User is not allowed to add checkins")
    if contest.creator.user.id is not request.user.id:
        logger.warning("User %s attempted to validate checkins " +
                       "for contest '%s' that they do not own",
                       request.user.username, contest.name)
        raise PermissionDenied("User is not allowed to add checkins")
    contest_player = Contest_Player.objects.get(contest_id=contest.id, 
                                                player_id=contest.creator.id)
    untappd_url = request.POST.get('untappd_url', None)
    if untappd_url is None:
        return render(request, 'beers/contest.html', 
                      context={ 'errors': ['No URL provided'],
                                'contest': contest,
                                'contest_player': contest_player,
                                'is_creator': True,
                                'activetab': 'checkins',},
                      status=400)
    if Unvalidated_Checkin.objects.filter(contest_player__contest_id=contest_id, 
                                          untappd_checkin=untappd_url).count() > 0:
        return render(request, 'beers/contest.html', 
                      context={ 'errors': ['Checkin with that URL already exists'],
                                'contest': contest,
                                'contest_player': contest_player,
                                'activetab': 'checkins',},
                      status=400)
    try:
        uv = parse_checkin(untappd_url)
        player = Contest_Player.objects.get(contest_id=contest_id, 
                                            player__untappd_username=uv.untappd_user)
        uv.contest_player = player
        uv.save()
        logger.info('Saved unvalidated checkin at url: {}'.format(uv.untappd_checkin))
        return render(request, 'beers/contest.html',
                      context={ 'contest': contest,
                                'contest_player': contest_player,
                                'is_creator': True,
                                'activetab': 'checkins', 
                                'unvalidated_checkin': uv, })
    except UntappdParseException as e:
        return render(request, 'beers/contest.html', 
                      context={ 'errors': ['Error parsing Untappd URL: {}'.format(e)],
                                'contest': contest,
                                'contest_player': contest_player,
                                'activetab': 'checkins',},
                      status=400)
    except Contest_Player.DoesNotExist:
        return render(request, 'beers/contest.html', 
                      context={ 'errors': ["The player associated with that " +
                                           "login doesn't exist or isn't in the contest"],
                                'contest': contest,
                                'contest_player': contest_player,
                                'activetab': 'checkins',},
                      status=400)