import logging
from beers import models
from django.contrib.auth.models import User
from rest_framework import serializers, validators
from rest_framework.reverse import reverse

logger = logging.getLogger(__name__)

class PlayerIdentityHyperlink(serializers.HyperlinkedIdentityField):
    view_name = 'player-detail'

    def get_url(self, player, view_name, request, format):
        url_kwargs = { 
            'user__username': player.user.username,
        }
        return reverse(view_name, kwargs=url_kwargs, request=request, format=format)

class PlayerSerializer(serializers.HyperlinkedModelSerializer):
    serializer_url_field = PlayerIdentityHyperlink
    username = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = models.Player
        extra_kwargs = {
            'url': {'lookup_field': 'user__username'}
        }
        fields = ('id', 
                  'url',
                  'username', 
                  'personal_statement', 
                  'untappd_username',
                  'untappd_rss',)

class ContestCreatorHyperlink(serializers.HyperlinkedRelatedField):
    view_name = 'player-detail'

    def get_url(self, creator_id, view_name, request, format):
        creator = models.Player.objects.get(id=creator_id.pk)
        url_kwargs = {
            'user__username': creator.user.username,
        }
        return reverse(view_name, kwargs=url_kwargs, request=request, format=format)

class ContestSerializer(serializers.HyperlinkedModelSerializer):

    creator = ContestCreatorHyperlink(read_only=True,)
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

class ContestPlayerIdentityHyperlink(serializers.HyperlinkedIdentityField):
    view_name = 'contest-player-detail'

    def get_url(self, contest_player, view_name, request, format):
        url_kwargs = { 
            'contest_id': contest_player.contest.id,
            'username': contest_player.user_name,
        }
        return reverse(view_name, kwargs=url_kwargs, request=request, format=format)

class ContestToPlayerHyperlink(serializers.HyperlinkedRelatedField):
    view_name = 'player-detail'

    def get_url(self, player_id, view_name, request, format):
        player = models.Player.objects.get(id=player_id.pk)
        url_kwargs = { 
            'user__username': player.user.username,
        }
        return reverse(view_name, kwargs=url_kwargs, request=request, format=format)

class ContestPlayerSerializer(serializers.HyperlinkedModelSerializer):
    serializer_url_field = ContestPlayerIdentityHyperlink
    contest = serializers.HyperlinkedRelatedField(many=False,
                                                  read_only=True,
                                                  view_name='contest-detail',
                                                  lookup_field='id',)
    player = ContestToPlayerHyperlink(read_only=True,)
    username = serializers.ModelField(
            model_field=models.Contest_Player()._meta.get_field('user_name'))

    rank = serializers.IntegerField(read_only=True)

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
    queryset = models.Contest_Player.objects.all()

    def get_url(self, challenger_id, view_name, request, format):
        """
        Parses out the url for the challenger for a Contest Beer or Contest Brewery
        """
        # The object passed in is a PKOnlyObject, not the whole Contest_Player
        challenger = models.Contest_Player.objects.get(id=challenger_id.pk)
        url_kwargs = { 
            'contest_id': challenger.contest.id,
            'username': challenger.user_name,
        }
        return reverse(view_name, kwargs=url_kwargs, request=request, format=format)

    def get_object(self, view_name, view_args, view_kwargs):
        lookup_kwargs = { 
            'contest__id': view_kwargs['contest_id'],
            'user_name': view_kwargs['username'],
        }
        return self.get_queryset().get(**lookup_kwargs)

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
    brewery_url = serializers.URLField(source='beer.brewery_url')
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
        if 'challenger' in validated_data:
            key_names = ['point_value', 'challenge_point_value', 
                         'challenge_point_loss', 'max_point_loss']
            kwargs = { key: value for key, value in validated_data.items() \
                                  if key in key_names }
            return contest.add_challenge_beer(beer, validated_data['challenger'],
                                              **kwargs)
        else:
            return contest.add_beer(beer, validated_data.get('point_value', 1))

    def update(self, contest_beer, validated_data):
        errors = {}
        if contest_beer.beer.name != validated_data['beer']['name']:
            errors['name'] = ['Beer name cannot be changed through update']
        if contest_beer.beer.brewery != validated_data['beer']['brewery']:
            errors['brewery'] = ['Brewery name value cannot be changed through update']
        if contest_beer.brewery.untappd_url != validated_data['beer']['untappd_url']:
            errors['untappd_url'] = ['Untappd URL value cannot be changed through update']
        if len(errors) > 0:
            raise serializers.ValidationError(errors)
        contest_beer.point_value = validated_data['point_value']
        contest_beer.save()

class ContestBreweryHyperlink(serializers.HyperlinkedIdentityField):
    view_name = 'contest-brewery-detail'

    def get_url(self, contest_brewery, view_name, request, format):
        url_kwargs = { 
            'contest_id': contest_brewery.contest.id,
            'contest_brewery_id': contest_brewery.id,
        }
        return reverse(view_name, kwargs=url_kwargs, request=request, format=format)

class ContestBrewerySerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    url = ContestBreweryHyperlink(view_name='contest-brewery-detail',)
    name = serializers.CharField(required=True, max_length=250, source='brewery.name')
    untappd_url = serializers.URLField(source='brewery.untappd_url')
    location = serializers.CharField(required=False, 
                                     max_length=250, 
                                     source='brewery.location')
    point_value = serializers.IntegerField()
    total_visited = serializers.IntegerField(required=False, read_only=True,)

    def create(self, validated_data):
        contest = validated_data['contest']
        brewery = None
        brewery_filter = models.Brewery.objects.filter(
                name=validated_data['brewery']['name'],)
        if brewery_filter.exists():
            brewery = brewery_filter.get()
        else:
            brewery = models.Brewery.objects.create_brewery(**validated_data['brewery'])
        contest_brewery = contest.add_brewery(brewery, 
                                              validated_data.get('point_value', 1))
        return contest_brewery

    def update(self, contest_brewery, validated_data):
        errors = {}
        if contest_brewery.brewery.name != validated_data['brewery']['name']:
            errors['name'] = ['Brewery name cannot be changed through update']
        if contest_brewery.brewery.untappd_url != validated_data['brewery']['untappd_url']:
            errors['untappd_url'] = \
                ['Untappd URL value cannot be changed through update']
        if len(errors) > 0:
            raise serializers.ValidationError(errors)
        contest_brewery.point_value = validated_data['point_value']
        contest_brewery.save()

class ContestBonusHyperlink(serializers.HyperlinkedIdentityField):
    view_name = 'contest-bonus-detail'

    def get_url(self, contest_bonus, view_name, request, format):
        url_kwargs = { 
            'contest_id': contest_bonus.contest.id,
            'contest_bonus_id': contest_bonus.id,
        }
        return reverse(view_name, kwargs=url_kwargs, request=request, format=format)

class HashTagListField(serializers.ListField):
    child = serializers.CharField()

    def to_representation(self, hash_tags):
        return hash_tags.split(',')

class ContestBonusSerializer(serializers.HyperlinkedModelSerializer):
    serializer_url_field = ContestBonusHyperlink
    
    contest = serializers.HyperlinkedRelatedField(many=False, 
                                                  read_only=True,
                                                  view_name='contest-detail',
                                                  lookup_field='id',)

    def create(self, validated_data):
        bonus = validated_data['contest'].add_bonus(validated_data['name'],
                                                    validated_data['description'],
                                                    validated_data['hashtags'],
                                                    validated_data['point_value'],)
        return bonus
        
    class Meta:
        model = models.Contest_Bonus
        extra_kwargs = {
            'url': {'view_name': 'contest-bonus-detail', 'lookup_field': 'id'}
        }
        fields = ('id', 
                  'contest',
                  'url', 
                  'name',
                  'description', 
                  'hashtags',
                  'point_value',
                 )

class UnvalidatedCheckinToContestPlayerHyperlink(serializers.HyperlinkedRelatedField):
    view_name = "contest-player-detail"

    def get_url(self, contest_player_id, view_name, request, format):
        player = models.Contest_Player.objects.get(id=contest_player_id.pk)
        url_kwargs = {
            'contest_id': player.contest.id,
            'username': player.user_name,
        }
        return reverse(view_name, kwargs=url_kwargs, request=request, format=format)
        
class UnvalidatedCheckinSerializer(serializers.HyperlinkedModelSerializer):

    contest_player = UnvalidatedCheckinToContestPlayerHyperlink(read_only=True,)
    player = serializers.ReadOnlyField(source='contest_player.user_name')

    class Meta:
        model = models.Unvalidated_Checkin
        extra_kwargs = { 
            'url': { 'view_name': 'unvalidated-checkin-detail', 'lookup_field': 'id', } 
        }
        fields = ('url',
                  'id',
                  'contest_player', 
                  'player',
                  'untappd_title',
                  'untappd_checkin',
                  'untappd_checkin_date',
                  'brewery',
                  'beer',
                  'beer_url',
                  'brewery_url',
                  'photo_url',
                  'possible_bonuses',
                  'has_possibles',
                  'rating',)
        read_only_fields = ('id', 
                            'contest_player',
                            'player',
                            'untappd_title',
                            'untappd_checkin_date',
                            'brewery',
                            'beer',
                            'beer_url',
                            'brewery_url',
                            'photo_url',
                            'possible_bonuses',
                            'has_possibles',
                            'rating',)

    def create(self, validated_data):
        logger.info("In unvalidated checkin create()")
        unvalidated_checkin = models.Unvalidated_Checkin(
            contest_player=validated_data['contest_player'],
            untappd_title=validated_data['untappd_title'],
            untappd_checkin=validated_data['untappd_checkin'],
            untappd_checkin_date=validated_data['untappd_checkin_date'],
            beer=validated_data['beer'],
            brewery=validated_data['brewery'],
            beer_url=validated_data['beer_url'],
            brewery_url=validated_data['brewery_url'],
        )
        unvalidated_checkin.save()
        logger.info("Saved %s", unvalidated_checkin.untappd_checkin)
        return unvalidated_checkin
