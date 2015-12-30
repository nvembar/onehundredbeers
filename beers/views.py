from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse
from django.db import transaction
from django.contrib.auth import authenticate
from django.contrib.auth import views as auth_views
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import PermissionDenied
from .models import Contest
from .models import Beer
from .models import Player
from .models import Checkin
from .models import Contest_Beer
from .models import Contest_Player
from .forms.registration import RegistrationForm
from .forms.contests import ContestForm

class HttpNotImplementedResponse(HttpResponse):
	status_code = 501

def is_authenticated_user_contest_runner(request):
	"""Convenience method to check if the authenticated user is allowed to
	create contests"""
	return (request.user.is_authenticated()
		and len([g for g in request.user.groups.all() if g.name == 'G_ContestRunner']) > 0)

def index(request):
	contests = Contest.objects.order_by('created_on')[:5]
	context = { 'contests': contests }
	return render(request, 'beers/index.html', context)

def contests(request):
	contests = Contest.objects.order_by('created_on')
	context = { 'contests': contests,
	 			'allow_add': is_authenticated_user_contest_runner(request) }
	return render(request, 'beers/contests.html', context)

def contest(request, contest_id):
	contest = get_object_or_404(Contest, id=contest_id)
	contest_players = Contest_Player.objects.filter(contest_id=contest_id).order_by('-beer_count')
	contest_beers = Contest_Beer.objects.filter(contest_id =contest_id).order_by('beer_name')
	context = { 'contest': contest, 'players': contest_players, 'beers': contest_beers }
	return render(request, 'beers/contest.html', context)

def contest_add(request):
	f = None
	if request.method == 'POST':
		if not is_authenticated_user_contest_runner(request):
			raise PermissionDenied("User is not allowed to create new contests")
		f = ContestForm(request.POST)
		if f.is_valid():
			data = f.clean()
			creator = Player.objects.get(user_id=request.user.id)
			contest = Contest.objects.create_contest(data['name'],
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
	contest_player = get_object_or_404(Contest_Player.objects.select_related(),
		contest_id=contest_id, user_name=username)
	player_checkins = Checkin.objects.filter(player_id=contest_player.player.id).select_related().order_by('-checkin_time')
	context = { 'player': contest_player, 'checkins': player_checkins }
	return render(request, 'beers/contest-player.html', context)

def contest_beers(request, contest_id):
	return HttpNotImplementedResponse('Contest-Beer List not yet implemented')

def contest_beer(request, contest_id, beer_id):
	return HttpNotImplementedResponse('Contest-Beer Detail not yet implemented')

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
			user.save()
			player = Player.create(user,
				personal_statement=data.get('personal_statement'),
				untappd_rss=data.get('untappd_rss'))
			player.save()
			return render(request, 'registration/signup_success.html')
	else:
		f = RegistrationForm()
	return render(request, 'registration/signup.html', { 'form': f })
