"""Implementation of the Contest object for the application"""

import logging
import re
from django.db import models
from django.utils import timezone

logger = logging.getLogger(__name__)

class ContestManager(models.Manager):
    "Manager for contests"

    def create_contest(self, name, creator, start_date, end_date):
        """Creates a contest with defaults on active status, creation date,
        update date, beer count, and user count"""
        contest = self.create(name=name, creator=creator,
                              start_date=start_date, end_date=end_date,
                              active=False, created_on=timezone.now(),
                              last_updated=timezone.now(),
                              user_count=0, beer_count=0)
        # Add the creator as a player
        contest_player = contest.add_player(creator)
        return contest

class Contest(models.Model):
    "Represents a contest"
    from .player import Player

    name = models.CharField(max_length=250, unique=True)
    creator = models.ForeignKey(Player, default=1, on_delete=models.PROTECT)
    active = models.BooleanField(default=False)
    created_on = models.DateTimeField()
    last_updated = models.DateTimeField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    user_count = models.IntegerField(default=0)
    beer_count = models.IntegerField(default=0)

    objects = ContestManager()

    def add_player(self, player):
        """Adds a player into the contest - should deprecate link()"""
        from .contest_player import Contest_Player
        contest_player = Contest_Player(contest=self, player=player,
                                        user_name=player.user.username,
                                        beer_count=0,
                                        last_checkin_date=None,
                                        last_checkin_beer=None,
                                        last_checkin_load=self.start_date,)
        contest_player.save()
        return contest_player

    def add_beer(self, beer, point_value=1):
        """Adds a beer into the contest"""
        from .associations import Contest_Beer
        beer = Contest_Beer(contest=self, beer=beer,
                            beer_name=beer.name,
                            brewery_name=beer.brewery,
                            point_value=point_value,
                            total_drank=0,)
        beer.save()
        return beer

    def add_challenge_beer(self, beer, challenger,
                           point_value=3,
                           challenge_point_value=12,
                           challenge_point_loss=3,
                           max_point_loss=12):
        """
        Adds a new beer as a challenge with default values for the points.
        Challenge beers are associated with a player in the contest. By default,
        they will get 12 points for drinking the beer, but any other player
        will get 3 for drinking it and also have the challenger lose 3 points
        up to a maximum of 12 points lost
        """
        from .associations import Contest_Beer
        beer = Contest_Beer(contest=self, 
                            beer=beer,
                            challenger=challenger,
                            beer_name=beer.name,
                            point_value=point_value,
                            challenge_point_value=challenge_point_value,
                            challenge_point_loss=challenge_point_loss,
                            max_point_loss=max_point_loss,
                            total_drank=0,)
        beer.save()
        return beer

    def add_brewery(self, brewery, point_value=1):
        """Adds a brewery to the contest"""
        from .associations import Contest_Brewery
        brewery = Contest_Brewery(contest=self, brewery=brewery,
                                  brewery_name=brewery.name,
                                  point_value=point_value,)
        brewery.save()
        return brewery

    def __clean_hash_tags(self, hash_tags):
        """
        Takes either a string or an array of hash tags and returns a cleaned up
        list of hash tags or raises a ValueError if not formatted correctly
        """
        tag_list = None
        if isinstance(hash_tags, str):
            tag_list = [tag.strip() for tag in hash_tags.split(',')]
        elif isinstance(hash_tags, (list, tuple)):
            tag_list = [tag.strip() for tag in hash_tags]
        else:
            raise ValueError('The hash_tags object should be a list of strings or ' +\
                             'a comma-separated string of hash tags')
        tag_misses  = [tag for tag in tag_list if not re.fullmatch('[A-Za-z0-9_]+', tag)]
        if len(tag_misses) > 0:
            raise ValueError('A hash tag should only be made with letters, numbers ' +\
                             'and underscores: {}'.format(','.join(tag_misses)))
        return tag_list

    def __using_hash_tag(self, hash_tag):
        """
        Checks if a hash tag is already in use for this contest. Returns matching 
        bonus or None if no bonus exists.
        """
        from .associations import Contest_Bonus
        return Contest_Bonus.objects.filter(contest=self, 
                                            hashtags__contains=[hash_tag]).first()

    def add_bonus(self, name, description, hash_tags, point_value=1):
        """
        Adds a new bonus to the contest

        hash_tags can be a plain string, a comma-separated string, or an array of 
        strings
        """
        from .associations import Contest_Bonus
        tag_list = self.__clean_hash_tags(hash_tags)
        tag_matches = [(tag, self.__using_hash_tag(tag)) for tag in tag_list]
        tag_conflict = list(filter(lambda t: t[1] is not None, tag_matches))
        if len(tag_conflict) > 0:
            error_strings = ['#{} in {}'.format(t[0], t[1].name) for t in tag_conflict]
            raise ValueError('Hash tags are already being used: {}'.format(
                             ','.join(error_strings)))
        bonus = Contest_Bonus(contest=self, 
                              name=name,
                              description=description,
                              hashtags=tag_list,
                              point_value=point_value)
        bonus.save()
        return bonus

    def ranked_players(self):
        """
        Returns a list of players, in total_points ranked order, with an
        additional field 'rank' which includes the ranking of the player
        """
        from .contest_player import Contest_Player
        return Contest_Player.objects.raw('SELECT *, RANK() OVER ' +
                                          '(PARTITION BY contest_id ORDER BY ' +
                                          'total_points DESC) as rank FROM ' +
                                          'beers_contest_player WHERE ' +
                                          'contest_id = %s', [self.id])

    def beers(self, player=None):
        """
        Gets the list of beers in beer, brewery order. If the player is passed
        in, it adds a checked_into=True to the entry
        """
        from .associations import Contest_Beer
        from .contest_player import Contest_Checkin
        if player is None:
            return Contest_Beer.objects.filter(
                contest=self).order_by('beer_name')
        checkins = Contest_Checkin.objects.filter(contest_player__contest=self,
            contest_player__player=player,
            contest_beer=models.OuterRef('pk'))
        beers = Contest_Beer.objects.filter(contest=self).annotate(
            checked_into=models.Exists(checkins)).order_by('beer_name')
        return beers

    def breweries(self, player=None):
        """
        Gets the list of breweries in name order. If the player is passed
        in, it adds a checked_into=True to the entry
        """
        from .associations import Contest_Brewery
        from .contest_player import Contest_Checkin
        if player is None:
            return Contest_Brewery.objects.filter(
                contest=self).order_by('brewery_name')
        checkins = Contest_Checkin.objects.filter(contest_player__contest=self,
            contest_player__player=player,
            contest_brewery=models.OuterRef('pk'))
        breweries = Contest_Brewery.objects.filter(contest=self).annotate(
            checked_into=models.Exists(checkins)).order_by('brewery_name')
        return breweries

    def __str__(self):
        return self.name