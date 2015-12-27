from django.conf.urls import url

from . import views

urlpatterns = [
	url(r'^$', views.index, name='index'),
	url(r'^contests/$', views.contests, name='contests'),
	url(r'^contests/(?P<contest_id>[0-9]+)/$', views.contest, name='contest'),
	url(r'^contests/(?P<contest_id>[0-9]+)/players/(?P<username>[^/]+)$', views.contest_player, name='player-detail'),
	url(r'^contests/(?P<contest_id>[0-9]+)/beers/(?P<beer_id>[0-9]+)$', views.contest_beer, name='beer-detail'),
	url(r'^contests/(?P<contest_id>[0-9]+)/beers/$', views.contest_beers, name='beer-list')
]
