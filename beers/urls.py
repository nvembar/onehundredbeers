from django.conf.urls import url, include

from . import views

urlpatterns = [
	url(r'^$', views.index, name='index'),
	url(r'^', include('django.contrib.auth.urls')),
	url(r'^signup$', views.signup, name='signup'),
	url(r'^contests/$', views.contests, name='contests'),
	url(r'^contests/add$', views.contest_add, name='contest-add'),
	url(r'^contests/(?P<contest_id>[0-9]+)/$', views.contest, name='contest'),
	url(r'^contests/(?P<contest_id>[0-9]+)/join$', views.contest_join, name='contest-join'),
	url(r'^contests/(?P<contest_id>[0-9]+)/players/(?P<username>[^/]+)$', views.contest_player, name='player-detail'),
	url(r'^contests/(?P<contest_id>[0-9]+)/beers/(?P<beer_id>[0-9]+)$', views.contest_beer, name='beer-detail'),
	url(r'^contests/(?P<contest_id>[0-9]+)/beers/$', views.contest_beers, name='beer-list')
]
