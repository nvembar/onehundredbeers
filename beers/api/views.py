import logging
from beers import models
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User, Group
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics, permissions, serializers
from beers.api.serializers import PlayerSerializer, ContestSerializer, \
                                  ContestBrewerySerializer, \
                                  ContestBeerSerializer, ContestPlayerSerializer
import beers.utils.untappd as untappd

logger = logging.getLogger(__name__)

class PlayerList(generics.ListAPIView):
    """
    Lists all the players across all the games.
    """
    queryset = models.Player.objects.all()
    serializer_class = PlayerSerializer
    lookup_field = 'id'
    permission_fields = (permissions.IsAuthenticatedOrReadOnly,)

class PlayerDetail(generics.RetrieveUpdateAPIView):
    queryset = models.Player.objects.all()
    serializer_class = PlayerSerializer
    lookup_field = 'id'
    permission_fields = (permissions.IsAuthenticatedOrReadOnly,)

class IsContestRunnerPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.groups.filter(name='G_ContestRunner').exists()

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        player = models.Player.objects.get(user=request.user)
        contest = None
        if isinstance(obj, models.Contest):
            contest = obj
        elif isinstance(obj, models.Contest_Beer):
            contest = obj.contest
        elif isinstance(obj, models.Contest_Brewery):
            contest = obj.contest
        elif isinstance(obj, models.Contest_Player):
            contest = obj.contest
        elif isinstance(obj, models.Unvalidated_Checkin):
            contest = obj.contest_player.contest
        return contest.creator.id == player.id

class ContestList(generics.ListCreateAPIView):
    queryset = models.Contest.objects.all()
    serializer_class = ContestSerializer
    lookup_field = 'id'
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,
                          IsContestRunnerPermission,)

    def perform_create(self, serializer):
        creator = models.Player.objects.get(user=self.request.user)
        serializer.save(creator=creator)

class ContestDetail(generics.RetrieveUpdateAPIView):
    queryset = models.Contest.objects.all()
    serializer_class = ContestSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,
                          IsContestRunnerPermission,)
    lookup_field = 'id'

class ContestPlayerList(generics.ListCreateAPIView):
    queryset = models.Contest_Player.objects.all()
    serializer_class = ContestPlayerSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,
                          IsContestRunnerPermission,)

    def get_queryset(self):
        contest_id = self.kwargs['contest_id']
        return models.Contest_Player.objects.filter(
                contest__id=contest_id).order_by('-total_points', 'user_name')

class ContestPlayerDetail(generics.RetrieveAPIView):
    queryset = models.Contest_Player.objects.all()
    serializer_class = ContestPlayerSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,
                          IsContestRunnerPermission,)

    def get_object(self):
        contest_id = self.kwargs['contest_id']
        player_id = self.kwargs['player_id']
        contest_player = get_object_or_404(models.Contest_Player, 
                                           contest__id=contest_id,
                                           player__id=player_id,)
        return contest_player
        
class ContestBeerList(generics.ListCreateAPIView):
    queryset = models.Contest_Beer.objects.all()
    serializer_class = ContestBeerSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,
                          IsContestRunnerPermission,)

    def perform_create(self, serializer):
        contest_id = self.kwargs['contest_id']
        contest = models.Contest.objects.get(id=contest_id)
        beer_name = self.request.data['name']
        brewery_name = self.request.data['brewery']
        beer_filter = models.Beer.objects.filter(name=beer_name, brewery=brewery_name)
        # XXX: This should probably be moved into models.Contest.add_beer
        if contest.active:
            raise serializers.ValidationError(
                    {'non_field_errors': ['Cannot add beers to active contest']})
        if beer_filter.exists():
            beer = beer_filter.get()
            if models.Contest_Beer.objects.filter(beer=beer, contest=contest).exists():
                raise serializers.ValidationError(
                        {'non_field_errors': ['Duplicate beer/contest pairing']})
        serializer.save(contest=contest)

    def get_queryset(self):
        contest_id = self.kwargs['contest_id']
        return models.Contest_Beer.objects.select_related('beer', 
                'challenger').filter(contest__id=contest_id).order_by('beer_name')

class ContestBeerDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Contest_Beer.objects.all()
    serializer_class = ContestBeerSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,
                          IsContestRunnerPermission,)

    def perform_destroy(self, contest_beer):
        beer_id = contest_beer.beer.id
        contest_beer.delete()
        if models.Contest_Beer.objects.filter(beer__id=beer_id).count() == 0:
            # There are no other contest beers corresponding to the given Beer object
            # so we should delete the beer object
            models.Beer.objects.filter(id=beer_id).delete()
        
    def get_object(self):
        contest_id = self.kwargs['contest_id']
        contest_beer_id = self.kwargs['contest_beer_id']
        contest_beer = get_object_or_404(models.Contest_Beer, 
                                         contest__id = contest_id,
                                         id = contest_beer_id,)
        return contest_beer

class ContestBreweryList(generics.ListCreateAPIView):
    queryset = models.Contest_Brewery.objects.all()
    serializer_class = ContestBrewerySerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,
                          IsContestRunnerPermission,)

    def perform_create(self, serializer):
        contest_id = self.kwargs['contest_id']
        contest = models.Contest.objects.get(id=contest_id)
        name = self.request.data['name']
        brewery_filter = models.Brewery.objects.filter(name=name)
        # XXX: This should probably be moved into models.Contest.add_brewery
        if contest.active:
            raise serializers.ValidationError(
                    {'non_field_errors': ['Cannot add brewery to active contest']})
        if brewery_filter.exists():
            brewery = brewery_filter.get()
            if models.Contest_Brewery.objects.filter(
                        brewery=brewery, contest=contest).exists():
                raise serializers.ValidationError(
                        {'non_field_errors': ['Duplicate brewery/contest pairing']})
        serializer.save(contest=contest)

    def get_queryset(self):
        contest_id = self.kwargs['contest_id']
        return models.Contest_Brewery.objects.select_related('brewery',
                ).filter(contest__id=contest_id).order_by('brewery_name')

class ContestBreweryDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Contest_Brewery.objects.all()
    serializer_class = ContestBrewerySerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,
                          IsContestRunnerPermission,)

    def perform_destroy(self, contest_brewery):
        brewery_id = contest_brewery.brewery.id
        contest_brewery.delete()
        if models.Contest_Brewery.objects.filter(brewery__id=brewery_id).count() == 0:
            # There are no other contest breweries corresponding to the given 
            # Brewery object so we should delete the brewery object
            models.Brewery.objects.filter(id=brewery_id).delete()
        
    def get_object(self):
        contest_id = self.kwargs['contest_id']
        contest_brewery_id = self.kwargs['contest_brewery_id']
        contest_brewery = get_object_or_404(models.Contest_Brewery, 
                                            contest__id = contest_id,
                                            id = contest_brewery_id,)
        return contest_brewery

class BeerLookup(APIView):
    """Looking up beer data from Untappd from URL"""

    def get(self, request, format=None):
        """Retrieves beer info based on URL"""
        if 'url' not in request.query_params:
            raise serializers.ValidationError(
                    {'non_field_errors': ['No URL provided']})
        try:
            beer = untappd.parse_beer(request.query_params['url'])
            logger.info('Looking up beer at URL: %s', request.query_params['url'])
            beer_object = {'name': beer.name,
                           'brewery': beer.brewery,
                           'style': beer.style,
                           'untappd_url': beer.untappd_url,
                           'brewery_url': beer.brewery_url,
                          }
            return Response(beer_object)
        except untappd.UntappdParseException as e:
            raise serializers.ValidationError({'non_field_errors': ['{}'.format(e)]})

class BreweryLookup(APIView):
    """Looking up brewery data from Untappd from URL"""

    def get(self, request, format=None):
        """Retrieves beer info based on URL"""
        if 'url' not in request.query_params:
            raise serializers.ValidationError(
                    {'non_field_errors': ['No URL provided']})
        try:
            brewery = untappd.parse_brewery(request.query_params['url'])
            logger.info('Looking up brewery at URL: %s', request.query_params['url'])
            brewery_object = {'name': brewery.name,
                              'untappd_url': brewery.untappd_url,
                              'location': brewery.location,
                             }
            return Response(brewery_object)
        except untappd.UntappdParseException as e:
            raise serializers.ValidationError({'non_field_errors': ['{}'.format(e)]})


