from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse
from django.contrib.auth import authenticate
from django.contrib.auth import views as auth_views
from django.contrib.auth.forms import AuthenticationForm
from .models import Contest
from .models import Beer
from .models import Player
from .models import Checkin
from .models import Contest_Beer
from .models import Contest_Player

class HttpNotImplementedResponse(HttpResponse):
	status_code = 501

# Create your views here.
def index(request):
	contests = Contest.objects.order_by('created_on')[:5]
	context = { 'contests': contests }
	return render(request, 'beers/index.html', context)

def contests(request):
	contests = Contest.objects.order_by('created_on')
	context = { 'contests': contests }
	return render(request, 'beers/contests.html', context)

def contest(request, contest_id):
	contest = get_object_or_404(Contest, id=contest_id)
	contest_players = Contest_Player.objects.filter(contest_id=contest_id).order_by('-beer_count')
	contest_beers = Contest_Beer.objects.filter(contest_id =contest_id).order_by('beer_name')
	context = { 'contest': contest, 'players': contest_players, 'beers': contest_beers }
	return render(request, 'beers/contest.html', context)

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
