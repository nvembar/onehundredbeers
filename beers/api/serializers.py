from beers import models
from django.contrib.auth.models import User
from rest_framework import serializers, validators
from rest_framework.reverse import reverse

class PlayerSerializer(serializers.HyperlinkedModelSerializer):
    username = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = models.Player
        extra_kwargs = {
            'url': {'lookup_field': 'id'}
        }
        fields = ('id', 
                  'url',
                  'username', 
                  'personal_statement', 
                  'untappd_username',
                  'untappd_rss',)

class ContestSerializer(serializers.HyperlinkedModelSerializer):

    creator = serializers.HyperlinkedRelatedField(many=False, 
                                                  read_only=True,
                                                  view_name='player-detail',
                                                  lookup_field='id',)
    active = serializers.ReadOnlyField()
    created_on = serializers.ReadOnlyField()
    last_updated = serializers.ReadOnlyField()
    user_count = serializers.ReadOnlyField()
    beer_count = serializers.ReadOnlyField()

    def validate(self, data):
        if data['start_date'] > data['end_date']:
            raise serializers.ValidationError('Start date must be before end date')
        return data

    def create(self, validated_data):
        contest = models.Contest.objects.create_contest(validated_data['name'], 
                                                        validated_data['creator'],
                                                        validated_data['start_date'],
                                                        validated_data['end_date'],)
        return contest

    class Meta:
        model = models.Contest
        extra_kwargs = {
            'url': {'lookup_field': 'id'}
        }
        fields = ('id', 
                  'url', 
                  'name',
                  'creator', 
                  'start_date',
                  'end_date',
                  'active', 
                  'created_on', 
                  'last_updated',
                  'user_count',
                  'beer_count',)

class ContestPlayerHyperlink(serializers.HyperlinkedIdentityField):
    view_name = 'contest-player-detail'

    def get_url(self, contest_player, view_name, request, format):
        url_kwargs = { 
            'contest_id': contest_player.contest.id,
            'player_id': contest_player.player.id,
        }
        return reverse(view_name, kwargs=url_kwargs, request=request, format=format)


class ContestPlayerSerializer(serializers.HyperlinkedModelSerializer):
    serializer_url_field = ContestPlayerHyperlink
    contest = serializers.HyperlinkedRelatedField(many=False,
                                                  read_only=True,
                                                  view_name='contest-detail',
                                                  lookup_field='id',)
    player = serializers.HyperlinkedRelatedField(many=False,
                                                 read_only=True,
                                                 view_name='player-detail',
                                                 lookup_field='id',)
    username = serializers.ModelField(
            model_field=models.Contest_Player()._meta.get_field('user_name'))

    class Meta:
        model = models.Contest_Player
        extra_kwargs = {
            'url': { 'view_name': 'contest-player-detail' }
        }
        fields = ('id',
                  'url',
                  'contest', 
                  'player', 
                  'username', 
                  'beer_count', 
                  'beer_points',
                  'brewery_points',
                  'bonus_points',
                  'challenge_point_gain',
                  'challenge_point_loss',
                  'total_points',
                  'last_checkin_date',
                  'last_checkin_beer',
                  'last_checkin_brewery',
                  'last_checkin_load',
                  'rank',)

class ChallengerHyperlink(serializers.HyperlinkedRelatedField):
    view_name = 'contest-player-detail'

    def get_url(self, challenger_id, view_name, request, format):
        """
        Parses out the url for the challenger for a Contest Beer
        """
        # The object passed in is a PKOnlyObject, not the whole Contest_Player
        challenger = models.Contest_Player.objects.get(id=challenger_id.pk)
        url_kwargs = { 
            'contest_id': challenger.contest.id,
            'player_id': challenger.player.id,
        }
        return reverse(view_name, kwargs=url_kwargs, request=request, format=format)

class ContestBeerHyperlink(serializers.HyperlinkedIdentityField):
    view_name = 'contest-beer-detail'

    def get_url(self, contest_beer, view_name, request, format):
        url_kwargs = { 
            'contest_id': contest_beer.contest.id,
            'contest_beer_id': contest_beer.id,
        }
        return reverse(view_name, kwargs=url_kwargs, request=request, format=format)

class ContestBeerSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    url = ContestBeerHyperlink(view_name='contest-beer-detail',)
    name = serializers.CharField(required=True, max_length=250, source='beer.name')
    brewery = serializers.CharField(required=True, max_length=250, source='beer.brewery')
    untappd_url = serializers.URLField(source='beer.untappd_url')
    brewery_city = serializers.CharField(required=False, 
                                         max_length=250, 
                                         source='beer.brewery_city')
    brewery_state = serializers.CharField(required=False,
                                          max_length=250, 
                                          source='beer.brewery_state')
    brewery_lat = serializers.FloatField(required=False, source='beer.brewery_lat')
    brewery_lon = serializers.FloatField(required=False, source='beer.brewery_lon')
    point_value = serializers.IntegerField()
    challenger = ChallengerHyperlink(view_name='contest-player-detail', 
                                     read_only=True,
                                     required=False,)
    challenge_point_loss = serializers.IntegerField(required=False,)
    max_point_loss = serializers.IntegerField(required=False,)
    challenge_point_value = serializers.IntegerField(required=False,)
    total_drank = serializers.IntegerField(required=False, read_only=True,)

    def create(self, validated_data):
        contest = validated_data['contest']
        beer = None
        beer_filter = models.Beer.objects.filter(
                name=validated_data['beer']['name'],
                brewery=validated_data['beer']['brewery'])
        if beer_filter.exists():
            beer = beer_filter.get()
        else:
            beer = models.Beer.objects.create_beer(**validated_data['beer'])
        contest_beer = contest.add_beer(beer, validated_data.get('point_value', 1))
        return contest_beer

    def update(self, validated_data):
        pass
