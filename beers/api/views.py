from beers import models
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics, permissions
from beers.api.serializers import PlayerSerializer, ContestSerializer, \
                                  ContestPlayerSerializer


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

class ContestList(generics.ListAPIView):
    queryset = models.Contest.objects.all()
    serializer_class = ContestSerializer
    lookup_field = 'id'

class ContestDetail(generics.RetrieveUpdateAPIView):
    queryset = models.Contest.objects.all()
    serializer_class = ContestSerializer
    lookup_field = 'id'

class ContestPlayerList(generics.ListCreateAPIView):
    queryset = models.Contest_Player.objects.all()
    serializer_class = ContestPlayerSerializer

    def get_queryset(self):
        contest_id = self.kwargs['contest_id']
        return models.Contest_Player.objects.filter(
                contest__id=contest_id).order_by('-total_points', 'user_name')

class ContestPlayerDetail(generics.RetrieveAPIView):
    queryset = models.Contest_Player.objects.all()
    serializer_class = ContestPlayerSerializer

    def get_object(self):
        contest_id = self.kwargs['contest_id']
        player_id = self.kwargs['player_id']
        contest_player = get_object_or_404(models.Contest_Player, 
                                           contest__id=contest_id,
                                           player__id=player_id,)
        return contest_player
        
