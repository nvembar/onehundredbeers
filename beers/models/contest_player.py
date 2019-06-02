"""Models supporting One Hundred Beers"""

import datetime
import logging
from django.db import models, connection
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from .player import Player
from .drinks import Beer, Brewery

logger = logging.getLogger(__name__)

class Contest_Player(models.Model):
    """ Links a player's activities relative to a contest
        A reverse sort by contest and beer count gives you a leaderboard"""
    from .contest import Contest
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    user_name = models.CharField(max_length=50)
    beer_count = models.IntegerField(default=0)
    beer_points = models.IntegerField(default=0)
    brewery_points = models.IntegerField(default=0)
    bonus_points = models.IntegerField(default=0)
    challenge_point_gain = models.IntegerField(default=0)
    challenge_point_loss = models.IntegerField(default=0)
    total_points = models.IntegerField(default=0)
    last_checkin_date = models.DateTimeField(
        "Denormalized date from last checkin", null=True, blank=True)
    last_checkin_beer = models.CharField(
        "Denormalized beer name from last checkin",
        null=True,
        max_length=250,
        blank=True)
    last_checkin_brewery = models.CharField(
        "Denormalized brewery name from last checkin",
        null=True,
        max_length=250,
        blank=True)
    last_checkin_load = models.DateTimeField(
        "Latest date in the last load for this player")

    class Meta:
        unique_together = (('contest', 'player'),)

    def __compute_losses(self):
        """
        Computes the point value of the losses due to challenges. We do need
        to query against the set of data (at the moment) because calculating
        against the maximum point loss requires querying against all the
        checkouts of all the challenge beers.
        """
        challenger_losses = Contest_Checkin.objects.filter(contest_player=self, 
                                                           tx_type='CL')
        loss = (challenger_losses.aggregate(
            models.Sum('checkin_points'))['checkin_points__sum'] or 0)
        self.challenge_point_loss = -loss
        self.save()

    def drink_beer(self, beer, checkin=None, data=None):
        """
        Has the user check in to a beer, using the data from a checkin or
        from a dictionary. This does all the calculations for points,
        challenges, and updates history. It does not delete the checkin and
        gives preference to the data from the data object.

        beer: A Contest_Beer object to check into
        checkin: An Unvalidated_Checkin object

        returns Contest_Checkin
        """
        if beer.contest.id != self.contest.id:
            raise ValueError('Cannot check into a beer not in the contest')
        checkin_time = None
        untappd_checkin = None
        if checkin:
            if checkin.contest_player.id != self.id:
                raise ValueError('Player and checkin not matched')
            checkin_time = checkin.untappd_checkin_date
            untappd_checkin = checkin.untappd_checkin
        if data is not None:
            if 'checkin_time' in data:
                checkin_time = data['checkin_time']
            if 'untappd_checkin' in data:
                untappd_checkin = data['untappd_checkin']
        logger.info("contest_player(%s).drink_beer: beer %s, checkin: %s", 
                    self.user_name, beer.beer_name, untappd_checkin)
        self.last_checkin_date = checkin_time
        self.last_checkin_beer = beer.beer_name
        self.last_checkin_brewery = None
        # Check if the beer has already been checked in
        # Exclude the CL type as that indicates that another use drank the beer
        if Contest_Checkin.objects.filter(contest_player=self,
                                          contest_beer=beer).exclude(tx_type='CL').count() > 0:
            logger.info("contest_player(%s).drink_beer: Already checked into beer %s",
                        self.user_name, beer.beer_name)
            return None
        checkin = None
        # Check if this is a challenge beer
        if beer.challenger is not None:
            # This is our own challenge beer, so
            if beer.challenger.id == self.id:
                logger.info("contest_player(%s).drink_beer: Adding self-drink challenge beer %s",
                            self.user_name, untappd_checkin)
                checkin = Contest_Checkin(contest_player=self,
                                          contest_beer=beer,
                                          checkin_points=beer.challenge_point_value,
                                          untappd_checkin=untappd_checkin,
                                          checkin_time=checkin_time,
                                          tx_type='CS',
                                         )
                checkin.save()
                self.challenge_point_gain = (self.challenge_point_gain
                                             + beer.challenge_point_value)
            else:
                logger.info("contest_player(%s).drink_beer: Adding other-drinnk challenge beer %s",
                            self.user_name, untappd_checkin)
                checkin = Contest_Checkin(contest_player=self,
                                          contest_beer=beer,
                                          checkin_points=beer.point_value,
                                          untappd_checkin=untappd_checkin,
                                          checkin_time=checkin_time,
                                          tx_type='CO',
                                         )
                checkin.save()
                self.beer_points = self.beer_points + beer.point_value
                # The challenger is penalized if someone else drinks their
                # challenge beer
                challenger = beer.challenger
                points_lost = (Contest_Checkin.objects.filter(contest_player=challenger,
                    contest_beer=beer,
                    tx_type='CL').aggregate(
                        models.Sum('checkin_points'))['checkin_points__sum'] or 0)
                if -(points_lost - beer.challenge_point_loss) <= beer.max_point_loss:
                    loss_checkin = Contest_Checkin(
                        contest_player=challenger,
                        contest_beer=beer,
                        checkin_points=-beer.challenge_point_loss,
                        checkin_time=checkin_time,
                        untappd_checkin=untappd_checkin,
                        tx_type='CL',
                        )
                    loss_checkin.save()

                challenger.__compute_losses()
                challenger.total_points = (challenger.beer_points
                                           + challenger.brewery_points
                                           + challenger.bonus_points
                                           + challenger.challenge_point_gain
                                           - challenger.challenge_point_loss)
                challenger.save()
        else:
            logger.info("contest_player(%s).drink_beer: Adding drink non-challenge beer %s",
                            self.user_name, untappd_checkin)
            checkin = Contest_Checkin(contest_player=self,
                                      contest_beer=beer,
                                      checkin_points=beer.point_value,
                                      untappd_checkin=untappd_checkin,
                                      checkin_time=checkin_time,
                                      tx_type='BE',
                                     )
            checkin.save()
            self.beer_points = self.beer_points + beer.point_value
        self.total_points = (self.brewery_points
                             + self.beer_points
                             + self.bonus_points
                             + self.challenge_point_gain
                             - self.challenge_point_loss)
        self.beer_count = self.beer_count + 1
        self.save()
        return checkin

    def drink_at_brewery(self, brewery, checkin=None, data=None):
        """
        Has the user check in to a brewery, using the data from a checkin or
        from a dictionary. It does not delete the checkin and gives preference
        to the data from the data object.

        brewery: a Contest_Brewery object to check into
        checkin: an Unvalidated_Checkin object

        returns Contest_Checkin
        """
        if brewery.contest.id != self.contest.id:
            raise ValueError('Cannot check into a brewery not in the contest')
        checkin_time = None
        untappd_checkin = None
        if checkin:
            if checkin.contest_player.id != self.id:
                raise ValueError('Cannot use checkin not in the contest')
            checkin_time = checkin.untappd_checkin_date
            untappd_checkin = checkin.untappd_checkin
        if data is not None:
            if 'checkin_time' in data:
                checkin_time = data['checkin_time']
            if 'untappd_checkin' in data:
                untappd_checkin = data['untappd_checkin']
        self.last_checkin_date = checkin_time
        self.last_checkin_beer = None
        self.last_checkin_brewery = brewery.brewery_name
        if Contest_Checkin.objects.filter(contest_player=self,
                                          contest_brewery=brewery).count() > 0:
            return None
        checkin = Contest_Checkin(contest_player=self,
                                  contest_brewery=brewery,
                                  checkin_points=brewery.point_value,
                                  untappd_checkin=untappd_checkin,
                                  checkin_time=checkin_time,
                                  tx_type='BR',
                                 )
        checkin.save()
        self.brewery_points = self.brewery_points + brewery.point_value
        self.total_points = self.total_points + brewery.point_value
        self.save()
        return checkin

    def drink_bonus(self, bonus, checkin=None, data=None):
        """
        Has the user check in to a bonus, using the data from a checkin or
        from a dictionary. It does not delete the checkin and gives preference
        to the data from the data object.

        bonus: a string bonus tag to check into
        checkin: an Unvalidated_Checkin object

        returns Contest_Checkin
        """
        from .associations import Contest_Bonus
        checkin_time = None
        untappd_checkin = None
        contest_bonus = None
        try:
            contest_bonus = Contest_Bonus.objects.get(contest=self.contest,
                                                      name=bonus)
        except Contest_Bonus.DoesNotExist:
            raise ValueError('No such bonus {} for contest'.format(bonus))
        if checkin:
            if checkin.contest_player.id != self.id:
                raise ValueError('Cannot use checkin not in the contest')
            checkin_time = checkin.untappd_checkin_date
            untappd_checkin = checkin.untappd_checkin
        if data is not None:
            if 'checkin_time' in data:
                checkin_time = data['checkin_time']
            if 'untappd_checkin' in data:
                untappd_checkin = data['untappd_checkin']
        
        checkin = Contest_Checkin(contest_player=self,
                                  contest_bonus=contest_bonus,
                                  checkin_points=contest_bonus.point_value,
                                  untappd_checkin=untappd_checkin,
                                  checkin_time=checkin_time,
                                  tx_type='BO',
                                 )
        checkin.save()
        self.bonus_points = self.bonus_points + contest_bonus.point_value
        self.total_points = self.total_points + contest_bonus.point_value
        self.save()
        return checkin

    def compute_points(self):
        """Computes the brewery and beer points for this user."""
        checkins = Contest_Checkin.objects.filter(contest_player=self)
        self.challenge_point_gain = checkins.filter(tx_type='CS').aggregate(
            models.Sum('checkin_points'))['checkin_points__sum'] or 0
        self.challenge_point_loss = -(checkins.filter(tx_type='CL').aggregate(
            models.Sum('checkin_points'))['checkin_points__sum'] or 0)
        self.beer_points = checkins.filter(models.Q(tx_type='CO') | 
                                             models.Q(tx_type='BE')).aggregate(
            models.Sum('checkin_points'))['checkin_points__sum'] or 0
        self.brewery_points = checkins.filter(tx_type='BR').aggregate(
            models.Sum('checkin_points'))['checkin_points__sum'] or 0
        self.bonus_points = checkins.filter(tx_type='BO').aggregate(
            models.Sum('checkin_points'))['checkin_points__sum'] or 0
        self.total_points = (self.beer_points
                             + self.brewery_points
                             + self.bonus_points
                             + self.challenge_point_gain
                             - self.challenge_point_loss)
        self.save()

    def find_possible_matches(self):
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE beers_unvalidated_checkin uv
                   SET has_possibles = TRUE
                  FROM beers_contest_beer b
                 WHERE uv.contest_player_id = %s
                   AND b.contest_id = %s
                   AND b.beer_name = uv.beer
                   AND b.brewery_name = uv.brewery
                """, [self.id, self.contest_id])
                            
    def __str__(self):
        return "{0}:[Player={1}]".format(self.contest.name, self.user_name)

class Contest_CheckinManager(models.Manager):
    def create_checkin(self, contest_player, contest_beer, checkin_time,
                       untappd_checkin):
        cc = self.create(contest_player=contest_player,
                         contest_beer=contest_beer,
                         checkin_time=checkin_time,
                         checkin_points=contest_beer.point_value,
                         untappd_checkin=untappd_checkin)
        return cc

    def create_brewery_checkin(self, contest_player, contest_brewery,
                               checkin_time, untappd_checkin):
        return self.create(contest_player=contest_player,
                           contest_brewery=contest_brewery,
                           checkin_time=checkin_time,
                           checkin_points=contest_brewery.point_value,
                           untappd_checkin=untappd_checkin)

class Contest_Checkin(models.Model):
    from .associations import Contest_Beer, Contest_Bonus, Contest_Brewery
    TRANSACTION_TYPES = (
        ('BE', 'Beer'),
        ('BR', 'Brewery'),
        ('CO', 'Challenge Beer - Other'),
        ('CS', 'Challenge Beer - Self'),
        ('CL', 'Challenge Beer - Loss'),
        ('BO', 'Bonus'),
    )
    tx_type = models.CharField(max_length=2, default='BE', choices=TRANSACTION_TYPES)
    contest_player = models.ForeignKey(Contest_Player, on_delete=models.CASCADE)
    contest_beer = models.ForeignKey(Contest_Beer, 
                                     on_delete=models.CASCADE, 
                                     blank=True, 
                                     null=True,
                                    )
    contest_brewery = models.ForeignKey(Contest_Brewery,
                                        on_delete=models.CASCADE,
                                        blank=True,
                                        null=True,
                                       )
    contest_bonus = models.ForeignKey(Contest_Bonus,
                                      on_delete=models.CASCADE,
                                      blank=True,
                                      null=True)
    bonus_type = models.CharField(max_length=10, blank=True, null=True,)
    checkin_points = models.IntegerField(default=1)
    checkin_time = models.DateTimeField()
    untappd_checkin = models.URLField(max_length=250, null=True, blank=True)

    objects = Contest_CheckinManager()

    def description(self):
        """Returns a string that describes what got or lost the user points"""
        if self.tx_type == 'BE':
            return "Drank {} by {}".format(self.contest_beer.beer.name, 
                                           self.contest_beer.beer.brewery)
        elif self.tx_type == 'BR':
            return "Drank at {}".format(self.contest_brewery.brewery.name)
        elif self.tx_type == 'CO':
            return "Drank {}'s challenge - {} by {}".format(
                self.contest_beer.challenger.user_name,
                self.contest_beer.beer.name,
                self.contest_beer.beer.brewery)
        elif self.tx_type == 'CS':
            return "Drank own challenge beer - {} by {}".format(
                self.contest_beer.beer.name,
                self.contest_beer.beer.brewery)
        elif self.tx_type == 'CL':
            return "Lost points to competitor drinking challenge beer"
        elif self.tx_type == 'BO':
            return "Got bonus '{}' points".format(self.contest_bonus.name)

