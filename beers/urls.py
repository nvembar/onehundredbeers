"""URL definition for the beer site"""


from django.urls import path, include
from beers.views import user, validation, contest, checkin
import beers.api.views as api_views

api_patterns = [
    path('players/', api_views.PlayerList.as_view(), name='player-list',),
    path('players/<slug:user__username>', api_views.PlayerDetail.as_view(), name='player-detail',),
    path('contests/', api_views.ContestList.as_view(), name='contest-list',),
    path('contests/<int:id>', api_views.ContestDetail.as_view(), name='contest-detail',),
    path('contests/<int:contest_id>/players/', 
         api_views.ContestPlayerList.as_view(), 
         name='contest-player-list',),
    path('contests/<int:contest_id>/players/<slug:username>',
         api_views.ContestPlayerDetail.as_view(),
         name='contest-player-detail',),
    path('contests/<int:contest_id>/beers/', 
         api_views.ContestBeerList.as_view(), 
         name='contest-beer-list',),
    path('contests/<int:contest_id>/beers/<int:contest_beer_id>',
         api_views.ContestBeerDetail.as_view(),
         name='contest-beer-detail',),
    path('contests/<int:contest_id>/breweries/',
         api_views.ContestBreweryList.as_view(),
         name='contest-brewery-list',),
    path('contests/<int:contest_id>/breweries/<int:contest_brewery_id>',
         api_views.ContestBreweryDetail.as_view(),
         name='contest-brewery-detail',),
    path('contests/<int:contest_id>/bonuses/',
         api_views.ContestBonusList.as_view(),
         name='contest-bonus-list',),
    path('contests/<int:contest_id>/bonuses/<int:contest_bonus_id>',
         api_views.ContestBonusDetail.as_view(),
         name='contest-bonus-detail',),
    path('contests/<int:contest_id>/unvalidated_checkins',
         api_views.UnvalidatedCheckinList.as_view(),
         name='unvalidated-checkin-list',),
    path('unvalidated_checkins/<int:id>',
         api_views.UnvalidatedCheckinDetail.as_view(),
         name='unvalidated-checkin-detail',),
    path('lookup/beer', api_views.BeerLookup.as_view(), name='beer-lookup'),
    path('lookup/brewery', api_views.BreweryLookup.as_view(), name='brewery-lookup'),
]

contest_patterns = [
    path('', contest.contests, name='contests'),
    path('add', contest.contest_add, name='contest-add'),
    path('<int:contest_id>/', include([
        path('', contest.contest, name='contest'),
        path('join', contest.contest_join, name='contest-join'),
        path('validate', validation.unvalidated_checkins, name='unvalidated-checkins'),
        path('unvalidated_checkins', 
             validation.unvalidated_checkins_json, 
             name='unvalidated-checkins-json'),
        path('unvalidated_checkins/<int:uv_checkin>', 
             validation.delete_checkin, 
             name='delete-checkin'),
        path('checkins', validation.validate_checkin, name='validate-checkin'),
        path('players/<slug:username>', contest.contest_player, name='contest-player'),
        path('players', contest.contest_players, name='contest-players'),
        path('beers/', contest.contest_beers, name='contest-beers'),
        path('beers/<int:beer_id>', contest.contest_beer, name='contest-beer'),
        path('breweries/', contest.contest_breweries, name='contest-breweries'),
        path('breweries/<int:brewery_id>', contest.contest_brewery, name='contest-brewery'),
        path('challenges/', contest.contest_challenges, name='contest-challenges'),
        path('challenges/<int:beer_id>', contest.contest_challenge, name='contest-challenge'),
        path('bonuses/', contest.contest_bonuses, name='contest-bonuses'),
        path('bonuses/<slug:bonus_tag>', contest.contest_bonus, name='contest-bonus'),
    ])),
]

urlpatterns = [
    path('', contest.index, name='index'),
    path('', include('django.contrib.auth.urls')),
    path('signup', user.signup, name='signup'),
    path('profile', user.update_profile, name='profile'),
    path('instructions', contest.instructions, name='instructions'),
    path('contests/', include(contest_patterns)),
    path('api/', include(api_patterns)),
]
