from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse
from django.db import transaction
from django.contrib.auth import authenticate
from django.contrib.auth import views as auth_views
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .views.helper import HttpNotImplementedResponse
from .views.helper import is_authenticated_user_player, is_authenticated_user_contest_runner
from .models import Contest
from .models import Beer
from .models import Player
from .models import Contest_Checkin
from .models import Contest_Beer
from .models import Contest_Player
from .models import Unvalidated_Checkin
from .forms.registration import RegistrationForm
from .forms.contests import ContestForm
import logging

logger = logging.getLogger(__name__)

def index(request):
	contests = Contest.objects.order_by('created_on')[:5]
	context = { 'contests': contests }
	return render(request, 'beers/index.html', context)

def contests(request):
	contests = Contest.objects.order_by('created_on')
	player = None
	if is_authenticated_user_player(request):
		try:
			player = Player.objects.get(user_id=request.user.id)
			# Add a field which indicates whether the logged in user is
			# already in a contest or can join it
			for c in contests:
				c.can_add = Contest_Player.objects.filter(
						player_id=player.id, contest_id=c.id).count() is 0
		except Player.DoesNotExist:
			pass
	context = { 'contests': contests,
	 			'allow_add': is_authenticated_user_contest_runner(request),
				'player': player }
	return render(request, 'beers/contests.html', context)

def contest(request, contest_id):
	contest = get_object_or_404(Contest, id=contest_id)
	context = { 'contest': contest }
	if request.user.is_authenticated:
		try:
			player = Player.objects.get(user_id=request.user.id)
			context['player'] = player
			if contest.creator.id == player.id:
				context['is_creator'] = True
		except:
			pass
	return render(request, 'beers/contest.html', context)

def contest_leaderboard(request, contest_id):
	contest = get_object_or_404(Contest, id=contest_id)
	contest_players = Contest_Player.objects.filter(contest_id=contest_id).order_by('-beer_count')
	context = { 'contest': contest, 'players': contest_players }
	return render(request, 'beers/contest-leaderboard.html', context)

def contest_add(request):
	"""Add a contest with a unique name to the list"""
	f = None
	if request.method == 'POST':
		if not is_authenticated_user_contest_runner(request):
			raise PermissionDenied("User is not allowed to create new contests")
		f = ContestForm(request.POST)
		if f.is_valid():
			data = f.clean()
			creator = Player.objects.get(user_id=request.user.id)
			contest = Contest.objects.create_contest(name=data['name'],
						creator=creator,
						start_date=data['start_date'],
						end_date=data['end_date'])
			contest.save()
			context = { 'contest': contest }
			return render(request, 'beers/contest-add-success.html', context)
	else:
		f = ContestForm()
	return render(request, 'beers/contest-add.html', { 'form': f })

def contest_player(request, contest_id, username):
	"""Shows the validated checkins for a player for a given contest"""
	contest_player = get_object_or_404(Contest_Player.objects.select_related(),
		contest_id=contest_id, user_name=username)
	player_checkins = Contest_Checkin.objects.filter(
		contest_player_id=contest_player.id).select_related().order_by('-checkin_time')
	context = { 'player': contest_player, 'checkins': player_checkins }
	return render(request, 'beers/contest-player.html', context)

def contest_beers(request, contest_id):
	contest = get_object_or_404(Contest, id=contest_id)
	contest_beers = None
	contest_player = None
	contest_beers = Contest_Beer.objects.filter(contest_id=contest_id)
	context = { 'contest': contest, 'contest_beers': contest_beers }
	if request.user.is_authenticated:
		try:
			contest_player = Contest_Player.objects.get(
				player__user_id=request.user.id)
			checkins = Contest_Checkin.objects.filter(
				contest_player_id=contest_player.id)
			checkin_ids = [c.contest_beer.id for c in checkins]
			for b in contest_beers:
				b.checked_into = b.id in checkin_ids
			context['contest_player'] = contest_player
		except:
			pass
	return render(request, 'beers/contest-beers.html', context)

def contest_beer(request, contest_id, beer_id):
	return HttpNotImplementedResponse('Contest-Beer Detail not yet implemented')

@login_required
@require_http_methods(['POST'])
def contest_join(request, contest_id):
	"""Add the logged in user to the contest"""
	contest = get_object_or_404(Contest, id=contest_id)
	if not is_authenticated_user_player(request):
		raise django.core.exceptions.PermissionDenied(
			'User {0} cannot join contests'.format(request.user.username))
	player = Player.objects.get(user_id=request.user.id)
	try:
		contest_player = Contest_Player.objects.get(contest_id=contest.id,
												player_id=player.id)
		context = { 'contest': contest, 'player': player, 'created_new': False }
	except Contest_Player.DoesNotExist:
		contest_player = Contest_Player.objects.link(contest, player)
		contest_player.save()
		context = { 'contest': contest, 'player': player, 'created_new': True }
	return render(request, 'beers/contest-join.html', context)

def instructions(request):
	return render(request, 'beers/instructions.html')

@transaction.atomic
def signup(request):
	f = None
	if request.method == 'POST':
		f = RegistrationForm(request.POST)
		if f.is_valid():
			# Create a new User and Player object
			data = f.clean()
			user = User.objects.create_user(data.get('username'),
					email=data.get('email'),
					first_name=data.get('first_name'),
					last_name=data.get('last_name'),
					password=data.get('password'))
			# Making an assumption that G_Player exists
			user.groups.add(Group.objects.get(name='G_Player'))
			user.save()
			player = Player.create(user,
				personal_statement=data.get('personal_statement'),
				untappd_rss=data.get('untappd_rss'))
			player.save()
			return render(request, 'registration/signup_success.html')
	else:
		f = RegistrationForm()
	return render(request, 'registration/signup.html', { 'form': f })