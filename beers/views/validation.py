from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse, HttpResponseBadRequest
from django.db import transaction
from django.contrib.auth import authenticate
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from beers.models import Contest
from beers.models import Beer
from beers.models import Player
from beers.models import Checkin
from beers.models import Contest_Checkin
from beers.models import Contest_Beer
from beers.models import Contest_Player
from beers.models import Unvalidated_Checkin
from beers.forms.contests import ValidateCheckinForm
from .helper import is_authenticated_user_contest_runner, is_authenticated_user_player
from .helper import HttpNotImplementedResponse
import logging

logger = logging.getLogger(__name__)

def BadValidationResponse(BaseException):
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
def checkin_validate(request, contest_id, uv_checkin):
	values = None
	try:
		values = align_contest_and_checkin(request, contest_id, uv_checkin)
	except BadValidationResponse as e:
		return HttpResponseBadRequest(e.value)
	uv = values['uv']
	contest = values['contest']
	possibles = Contest_Beer.objects.filter(contest_id=contest_id,
									beer__name__iexact=uv.beer)
	# Just get the first possible match
	form = None
	if possibles.count() > 0:
		logger.info("\tFound a possible match on checkin {0}: {1}/{2}"
					.format(uv.untappd_checkin, uv.beer, uv.brewery))
		form = ValidateCheckinForm(initial={ 'contest_beer': possibles[0].id })
	else:
		form = ValidateCheckinForm
	context = { 'uv': uv, 'contest': contest, 'form': form }
	return render(request, 'beers/validate-detail.html', context)

@login_required
@require_http_methods(['POST'])
@transaction.atomic
def update_checkin(request, contest_id, uv_checkin):
	values = None
	try:
		values = align_contest_and_checkin(request, contest_id, uv_checkin)
	except BadValidationResponse as e:
		return HttpResponseBadRequest(e.value)
	uv = values['uv']
	contest = values['contest']
	if request.POST.get('remove-beer') == 'Remove':
		uv.delete();
		if request.META.get('HTTP_ACCEPT') == 'application/json':
			return HttpResponse('{ "success": true }', content_type='application/json')
		else:
			return redirect('unvalidated-checkins', contest_id)
	contest_beer = None
	try:
		logger.info('Attempting to set UV {} to beer # {}'.format(uv.id, request.POST['contest_beer']))
		contest_beer = Contest_Beer.objects.get(id=int(request.POST['contest_beer']))
	except:
		return HttpResponseBadRequest(
			'No such beer with id %s'.format(request.POST.get('contest_beer')))
	if request.POST.get('validate-beer') == 'Validate':
		existing_cnt = Contest_Checkin.objects.filter(
				contest_player_id=uv.contest_player.id,
				contest_beer_id=contest_beer.id).count()
		# A truly new checkin
		if existing_cnt == 0:
			checkin = Contest_Checkin.objects.create_checkin(
					contest_player=uv.contest_player,
					contest_beer=contest_beer,
					checkin_time=uv.untappd_checkin_date,
					untappd_checkin=uv.untappd_checkin)
			checkin.save()
			uv.contest_player.beer_count = Contest_Checkin.objects.filter(
					contest_player_id=uv.contest_player.id).count()
			if (uv.contest_player.last_checkin_date is None or
					uv.untappd_checkin_date > uv.contest_player.last_checkin_date):
				uv.contest_player.last_checkin_date = uv.untappd_checkin_date
				uv.contest_player.last_checkin_beer = contest_beer.beer_name
			uv.contest_player.save()
		uv.delete()
		if request.META.get('HTTP_ACCEPT') == 'application/json':
			return HttpResponse('{ "success": true }', content_type='application/json')
		else:
			return redirect('unvalidated-checkins', contest_id)
	return HttpResponseBadRequest('No action taken on checkin %s'.format(uv.id))

@login_required
def unvalidated_checkins(request, contest_id):
	"""Presents all the unvalidated checkins to the contest runner for approval"""
	contest = get_object_or_404(Contest.objects, id=contest_id)
	if not is_authenticated_user_contest_runner(request):
		logger.warning("User {0} attempted to validate checkins for contest {1}"
					.format(request.user.name, contest_id))
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
	for uv in uvs:
		# Just get the first possible match
		possibles = Contest_Beer.objects.filter(contest_id=contest_id,
											beer__name__iexact=uv.beer)[:1]
		if possibles.count() > 0:
			logger.info("\tFound a possible match on checkin {0}: {1}/{2}"
							.format(uv.untappd_checkin, uv.beer, uv.brewery))
			uv.form = ValidateCheckinForm(
				initial={'contest_beer': possibles[0].id,
						 'auto_id': 'id_%s_'.format(uv.id) + '%s'})
			uv.contest_beer_id = possibles[0].id
			uv.beer_brewery = str(possibles[0].beer)
		else:
			uv.form = ValidateCheckinForm()
	context = { 'uvs': uvs, 'contest': contest, 'form': ValidateCheckinForm() }
	return render(request, 'beers/validate.html', context)
