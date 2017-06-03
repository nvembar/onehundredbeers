from django.conf.urls import url, include
from . import base_views
import beers.views.validation as validation
import beers.views.user as user

urlpatterns = [
	url(r'^$', base_views.index, name='index'),
	url(r'^', include('django.contrib.auth.urls')),
	url(r'^signup$', user.signup, name='signup'),
	url(r'^profile', user.update_profile, name='profile'),
	url(r'^contests/$', base_views.contests, name='contests'),
	url(r'^contests/add$', base_views.contest_add, name='contest-add'),
	url(r'^contests/(?P<contest_id>[0-9]+)/$', base_views.contest, name='contest'),
	url(r'^contests/(?P<contest_id>[0-9]+)/join$', base_views.contest_join, name='contest-join'),
	url(r'^contests/(?P<contest_id>[0-9]+)/validate$', validation.unvalidated_checkins, name='unvalidated-checkins'),
	url(r'^contests/(?P<contest_id>[0-9]+)/validate_api$', validation.unvalidated_checkins_json, name='unvalidated-checkins-json'),
	url(r'^contests/(?P<contest_id>[0-9]+)/validate/(?P<uv_checkin>[0-9]+)/update$', validation.update_checkin, name='update-checkin'),
	url(r'^contests/(?P<contest_id>[0-9]+)/players/(?P<username>[^/]+)$', base_views.contest_player, name='player-detail'),
	url(r'^contests/(?P<contest_id>[0-9]+)/beers/(?P<beer_id>[0-9]+)$', base_views.contest_beer, name='beer-detail'),
	url(r'^contests/(?P<contest_id>[0-9]+)/beers/$', base_views.contest_beers, name='beer-list'),
	url(r'^contests/(?P<contest_id>[0-9]+)/leaderboard/$', base_views.contest_leaderboard, name='leaderboard'),
	url(r'^contests/(?P<contest_id>[0-9]+)/recover$', validation.initiate_recover, name='initiate-recover'),
	url(r'^instructions$', base_views.instructions, name='instructions'),
]
