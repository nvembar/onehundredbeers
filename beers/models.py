"""Models supporting One Hundred Beers"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class PlayerManager(models.Manager):
    """A model manager for the Player object"""

    def create_player(self, user, personal_statement=None,
                      untappd_rss=None, untappd_username=None):
        """Creates a new player"""
        return self.create(user=user,
                           personal_statement=personal_statement,
                           untappd_rss=untappd_rss,
                           untappd_username=untappd_username)


# The user profile.
class Player(models.Model):
    "Represents a player profile"

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    personal_statement = models.CharField(max_length=150, blank=True, default='')
    city = models.CharField(max_length=150, blank=True, default='')
    untappd_username = models.CharField(max_length=150, blank=True, default='')
    untappd_rss = models.URLField(max_length=512, null=True, blank=True)

    objects = PlayerManager()

    def __str__(self):
        return self.user.username

class BeerManager(models.Manager):
    """Manages beer data"""
    def create_beer(self, name, brewery, style='', description='',
                    brewery_city='', brewery_state=''):
        """Creates a contest with defaults on active status, creation date,
        update date, beer count, and user count"""
        beer = self.create(name=name, brewery=brewery,
                           style=style, description=description,
                           brewery_city=brewery_city,
                           brewery_state=brewery_state,
                           last_updated=timezone.now())
        return beer

# Create your models here.
class Beer(models.Model):
    "Represents a common beer - can be shared across contests"

    name = models.CharField(max_length=250)
    brewery = models.CharField(max_length=250)
    style = models.CharField(max_length=250, null=True, blank=True, default='')
    description = models.CharField(max_length=250, null=True, blank=True, default='')
    brewery_city = models.CharField(max_length=250, null=True, blank=True, default='')
    brewery_state = models.CharField(max_length=250, null=True, blank=True, default='')
    brewery_country = models.CharField(max_length=250, null=True, blank=True, default='')
    brewery_lat = models.FloatField(null=True, blank=True)
    brewery_lon = models.FloatField(null=True, blank=True)
    untappd_id = models.CharField(max_length=25, null=True, blank=True)
    last_updated = models.DateTimeField()

    objects = BeerManager()

    def __str__(self):
        return self.name + ' / ' + self.brewery

class ContestManager(models.Manager):
    "Manager for contests"

    def create_contest(self, name, creator, start_date, end_date):
        """Creates a contest with defaults on active status, creation date,
        update date, beer count, and user count"""
        contest = self.create(name=name, creator=creator,
                              start_date=start_date, end_date=end_date,
                              active=True, created_on=timezone.now(),
                              last_updated=timezone.now(),
                              user_count=0, beer_count=0)
        return contest



class Contest(models.Model):
    "Represents a contest"

    name = models.CharField(max_length=250)
    creator = models.ForeignKey(Player, default=1)
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
        contest_player = Contest_Player(contest=self, player=player,
                                        user_name=player.user.username,
                                        beer_count=0,
                                        last_checkin_date=None,
                                        last_checkin_beer=None,
                                        last_checkin_load=self.start_date,
                                        rank=-1)
        contest_player.save()
        return contest_player

    def add_beer(self, beer, point_value=1):
        """Adds a beer into the contest"""
        beer = Contest_Beer(contest=self, beer=beer,
                            beer_name=beer.name,
                            point_value=point_value,
                            total_drank=0,)
        beer.save()
        return beer

    def add_challenge_beer(self, beer, challenger,
                           point_data={'point_value': 3,
                                       'challenge_point_value': 12,
                                       'point_loss': 3,
                                       'max_point_loss': 12, }):
        """
        Adds a new beer as a challenge with default values for the points.
        Challenge beers are associated with a player in the contest. By default,
        they will get 12 points for drinking the beer, but any other player
        will get 3 for drinking it and also have the challenger lose 3 points
        up to a maximum of 12 points lost
        """
        return None

    def add_brewery(self, brewery, point_value=1):
        """Adds a brewery to the contest"""
        brewery = Contest_Brewery(contest=self, brewery=brewery,
                                  brewery_name=brewery.name,
                                  point_value=point_value,)
        brewery.save()
        return brewery

    def ranked_players(self):
        """
        Returns a list of players, in total_points ranked order, with an
        additional field 'rank' which includes the ranking of the player
        """
        contest_players = Contest_Player.objects.filter(contest=self)
        contest_players = list(contest_players.order_by('-total_points',
                                                        'user_name'))
        max_points = Contest_Beer.objects.filter(contest=self).aggregate(
            models.Sum('point_value'))['point_value__sum']
        rank = 0
        # Start with rank 0 and a number higher than the highest possible beer
        # count. This forces the first iteration to step everything forward
        last_total_points = max_points + 1
        player_count = 0
        for p in contest_players:
            player_count = player_count + 1
            # Calculate the "1224" style ranking
            if p.total_points < last_total_points:
                rank = player_count
            p.rank = rank
            last_total_points = p.total_points
        return contest_players

    def beers(self, player=None):
        """
        Gets the list of beers in beer, brewery order. If the player is passed
        in, it adds a checked_into=True to the entry
        """
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


class Brewery_Manager(models.Manager):

    def create_brewery(self, name, untappd_id):
        return self.create(name=name, 
													 untappd_id=untappd_id,
													 last_updated=timezone.now())

class Brewery(models.Model):
    name = models.CharField(max_length=250)
    untappd_id = models.CharField(max_length=25, null=True, blank=True,)
    untappd_url = models.URLField(null=True, blank=True,)
    state = models.CharField(max_length=250)
    last_updated = models.DateTimeField()

    objects = Brewery_Manager()

    def __str__(self):
        return self.name

class Contest_BreweryManager(models.Manager):

    def link(self, contest, brewery, value):
        return self.create(contest=contest, brewery=brewery,
                           brewery_name=brewery.name,
                           point_value=value, total_drank=0,)

class Contest_Brewery(models.Model):
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE)
    brewery = models.ForeignKey(Brewery, on_delete=models.CASCADE)
    brewery_name = models.CharField(max_length=250)
    point_value = models.IntegerField(default=1)
    total_visited = models.IntegerField(default=0, 
			help_text="number of players who drank at this brewery")

    objects = Contest_BreweryManager()

    def __str__(self):
        return '{}/{}'.format(self.contest.name, self.brewery.name)

class Contest_Player(models.Model):
    """ Links a player's activities relative to a contest
        A reverse sort by contest and beer count gives you a leaderboard"""
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    user_name = models.CharField(max_length=50)
    beer_count = models.IntegerField(default=0)
    beer_points = models.IntegerField(default=0)
    brewery_points = models.IntegerField(default=0)
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
    rank = models.IntegerField(default=0)

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
        self.last_checkin_date = checkin_time
        self.last_checkin_beer = beer.beer_name
        self.last_checkin_brewery = None
        if Contest_Checkin.objects.filter(contest_player=self,
                                          contest_beer=beer).count() > 0:
            return None
        checkin = None
        # Check if this is a challenge beer
        if beer.challenger is not None:
            # This is our own challenge beer, so
            if beer.challenger.id == self.id:
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
                                           + challenger.challenge_point_gain
                                           - challenger.challenge_point_loss)
                challenger.save()
        else:
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
        self.total_points = (self.beer_points
                             + self.brewery_points
                             + self.challenge_point_gain
                             - self.challenge_point_loss)
        self.save()

    def __str__(self):
        return "{0}:[Player={1}]".format(self.contest.name, self.user_name)

class Contest_Beer(models.Model):
    "Represents a many-to-many connection between a beer and a contest"

    contest = models.ForeignKey(Contest, on_delete=models.CASCADE)
    challenger = models.ForeignKey(Contest_Player,
                                   on_delete=models.CASCADE,
                                   default=None,
                                   null=True,
                                  )
    beer = models.ForeignKey(Beer, on_delete=models.CASCADE)
    beer_name = models.CharField(max_length=250)
    point_value = models.IntegerField(default=1)
    challenge_point_loss = models.IntegerField(default=0)
    max_point_loss = models.IntegerField(default=0)
    challenge_point_value = models.IntegerField(
        default=0,
        help_text='The number of points the challenger gets ' +
            'for drinking this beer')
    total_drank = models.IntegerField("number of players who drank this beer")

    def __str__(self):
        return "{0}/{1}".format(self.beer.name, self.beer.brewery)

class Unvalidated_CheckinManager(models.Manager):
    def create_checkin(self, contest_player, untappd_title, brewery, beer,
                       untappd_checkin, untappd_checkin_date):
        return self.create(contest_player=contest_player,
                           untappd_title=untappd_title,
                           brewery=brewery,
                           beer=beer,
                           untappd_checkin=untappd_checkin,
                           untappd_checkin_date=untappd_checkin_date)

class Unvalidated_Checkin(models.Model):
    contest_player = models.ForeignKey(Contest_Player, on_delete=models.CASCADE)
    untappd_title = models.CharField(max_length=500, blank=False)
    untappd_checkin = models.URLField()
    untappd_checkin_date = models.DateTimeField()
    brewery = models.CharField(max_length=250, default='')
    beer = models.CharField(max_length=250, default='')

    objects = Unvalidated_CheckinManager()

    def __str__(self):
        return "Unvalidated checkin: {0}".format(self.untappd_title)

class Checkin(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    beer = models.ForeignKey(Beer, on_delete=models.CASCADE)
    checkin_time = models.DateTimeField()
    comment = models.CharField(max_length=250, null=True, blank=True, default='')
    rating = models.IntegerField(default=-1)
    untappd_checkin = models.URLField(max_length=250, null=True, blank=True)
    runner_validated = models.BooleanField(default=False)

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
    bonus_type = models.CharField(max_length=10, blank=True, null=True,)
    checkin_points = models.IntegerField(default=1)
    checkin_time = models.DateTimeField()
    untappd_checkin = models.URLField(max_length=250, null=True, blank=True)

    objects = Contest_CheckinManager()
