"""
Functions for viewing and editing contests
"""

import logging
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_http_methods
from beers.models import Contest, Player, Contest_Checkin, Contest_Beer, \
                         Contest_Brewery, Contest_Player
from beers.forms.contests import ContestForm
from .helper import HttpNotImplementedResponse
from .helper import is_authenticated_user_player, \
                    is_authenticated_user_contest_runner


logger = logging.getLogger(__name__)


def index(request):
    """Renders the index page with all the contest info"""
    all_contests = Contest.objects.order_by('-created_on')[:5]
    active = None
    if is_authenticated_user_contest_runner(request):
        player = Player.objects.get(user=request.user)
        for c in all_contests:
            if c.creator.id == player.id:
                c.is_creator = True
    context = {'contests': all_contests}
    if all_contests:
        active = all_contests[0]
        leaderboard = active.ranked_players()
        active.summary_leaderboard = leaderboard[0:5]
        context['active'] = active
    return render(request, 'beers/index.html', context)


@require_http_methods(['POST', 'GET'])
def contests(request):
    """
    Gets all contests or creates a new contest. 

    URL: /contests/

    GET:
    Returns all the contests 

    POST
    Creates a new contest in a inactive state

    Argument are: name, start_date, end_date as POST data or 
    { name: <name>, start_date: <start_date>, end_date: <end_date> } as JSON

    Returns data (as JSON or data in the page)
    { 
      name: <name>, 
      start_date: <start_date>, 
      end_date: <end_date>,
      last_updated: <date last updated>,
    }
    """
    all_contests = Contest.objects.order_by('created_on')
    player = None
    if is_authenticated_user_player(request):
        try:
            player = Player.objects.get(user_id=request.user.id)
            # Add a field which indicates whether the logged in user is
            # already in a contest or can join it
            for c in all_contests:
                c.can_add = Contest_Player.objects.filter(
                    player=player, contest=c).count() is 0
        except Player.DoesNotExist:
            pass
    context = {'contests': all_contests,
               'allow_add': is_authenticated_user_contest_runner(request),
               'player': player}
    return render(request, 'beers/contests.html', context)


def contest(request, contest_id):
    """
    Gets or edits the details of a specific contest and presents them to the user.

    URL: /contests/:id

    GET: Gets the details of the contest. For HTML response, by default, it returns 
    all the beer, brewery and challenge details. For JSON response, it returns the
    contest details

    PUT:
    Allows the user to edit the name, start date, end date, or active status of a 
    contest
    """
    this_contest = get_object_or_404(Contest, id=contest_id)
    ranked_players = this_contest.ranked_players()
    player = None
    this_contest_player = None
    is_creator = False
    if request.user.is_authenticated:
        try:
            player = Player.objects.get(user_id=request.user.id)
            this_contest_player = Contest_Player.objects.get(player=player,
                contest=this_contest)
            is_creator = this_contest.creator.id == player.id
        except Player.DoesNotExist:
            pass
    context = {'contest': this_contest,
               'contest_player': this_contest_player,
               'players': ranked_players,
               'contest_beers': this_contest.beers(player),
               'contest_breweries': this_contest.breweries(player),
               'is_creator': is_creator,
               }
    return render(request, 'beers/contest.html', context)


def contest_players(request):
    """
    Either gets the leaderboard for the given contest or allows the addition of a 
    new player to a contest.

    URL: /contest/:id/players

    GET: Gets the leaderboard for the contest. Allows for retrieval by JSON or HTML

    POST: Adds a player to the contest.
    """
    pass


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
            new_contest = Contest.objects.create_contest(name=data['name'],
                                                         creator=creator,
                                                         start_date=data['start_date'],
                                                         end_date=data['end_date'])
            new_contest.save()
            context = {'contest': new_contest}
            return render(request, 'beers/contest-add-success.html', context)
    else:
        f = ContestForm()
    return render(request, 'beers/contest-add.html', {'form': f})


def contest_player(request, contest_id, username):
    """
    Shows the data associated with a player or allows the contest runner to 
    remove a player from the game.

    URL: /contests/:id/players/:player

    GET: Gets the details of a given player in the context of a contest

    DELETE: Removes a player from a contest (does not delete the user)
    """
    cp = get_object_or_404(Contest_Player.objects.select_related(),
                           contest_id=contest_id,
                           user_name=username)
    player_checkins = Contest_Checkin.objects.filter(
        contest_player=cp).select_related().order_by('-checkin_time')
    context = {'player': cp, 'checkins': player_checkins}
    return render(request, 'beers/contest-player.html', context)


def contest_beer(request, contest_id, beer_id):
    """
    Gets the details of a beer for a contest, including its name, Untappd URL
    and the players who drank it, or allows for the editing of a beer in a contest, 
    including deletion.

    URL: /contests/:id/beers/:beer_id

    GET: Gets the details in HTML or JSON form

    PUT: Edits the details of a beer if the contest is not active

    DELETE: Removes the beer from a contest if the contest is not active
    """
    return HttpNotImplementedResponse('Contest-Beer Detail not yet implemented')


def contest_brewery(request, contest_id, brewery_id):
    """
    Gets the details of a brewery for a contest, including its name, Untappd URL
    and the players who drank at it, or allows for the editing of a brewery in a 
    contest, including deletion.

    URL: /contests/:id/breweries/:brewery_id

    GET: Gets the details in HTML or JSON form

    PUT: Edits the details of a brewery if the contest is not active

    DELETE: Removes the brewery from a contest if the contest is not active
    """
    return HttpNotImplementedResponse('Contest-Beer Detail not yet implemented')
    

def contest_challenge(request, contest_id, beer_id):
    """
    Gets the details of a challenge for a contest, including its name, Untappd URL
    and the players who drank at it, or allows for the editing of a brewery in a 
    contest, including deletion.

    URL: /contests/:id/challenges/:beer_id

    GET: Gets the details in HTML or JSON form

    PUT: Edits the details of a brewery if the contest is not active

    DELETE: Removes the challenge from a contest if the contest is not active
    """
    return HttpNotImplementedResponse('Contest-Beer Detail not yet implemented')


@login_required
@require_http_methods(['POST'])
def contest_join(request, contest_id):
    """Add the logged in user to the contest"""
    this_contest = get_object_or_404(Contest, id=contest_id)
    if not is_authenticated_user_player(request):
        raise django.core.exceptions.PermissionDenied(
            'User {0} cannot join contests'.format(request.user.username))
    player = Player.objects.get(user_id=request.user.id)
    if Contest_Player.objects.filter(contest=this_contest, player=player).count() != 0:
        context = {'contest': this_contest,
                   'player': player,
                   'created_new': False}
    else:
        this_contest.add_player(player)
        context = {'contest': contest, 'player': player, 'created_new': True}
    return render(request, 'beers/contest-join.html', context)


def instructions(request):
    """Returns the static instructions page"""
    return render(request, 'beers/instructions.html')
