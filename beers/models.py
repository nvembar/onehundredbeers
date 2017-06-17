from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import datetime

# The user profile.
class Player(models.Model):
	"Represents a player profile"

	user = models.OneToOneField(User, on_delete=models.CASCADE)
	personal_statement = models.CharField(max_length=150, blank=True, default='')
	city = models.CharField(max_length=150, blank=True, default='')
	untappd_username = models.CharField(max_length=150, blank=True, default='')
	untappd_rss = models.URLField(max_length=512, null=True, blank=True)

	# TODO: Move this to a manager
	@classmethod
	def create(cls, user, personal_statement=None, untappd_rss=None, untappd_username=None):
		player = cls(user=user, personal_statement=personal_statement,
				untappd_rss=untappd_rss, untappd_username=untappd_username)
		return player

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

	# XXX: Move this to Contest.add_beer
	def add_beer(self, contest, beer, point_value=1):
		contest_beer = Contest_Beer(contest=contest, beer=beer,
							beer_name=beer.name, point_value=point_value,
							total_drank=0,)
		return contest_beer


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

	def add_brewery(self, brewery, point_value=1):
		"Adds a brewery to the contest"
		cb = Contest_Brewery(contest=self, brewery=brewery,
				brewery_name=brewery.name, point_value=point_value,)
		cb.save()
		return cb

	def __str__(self):
		return self.name

class Contest_Beer(models.Model):
	"Represents a many-to-many connection between a beer and a contest"

	contest = models.ForeignKey(Contest, on_delete=models.CASCADE)
	beer = models.ForeignKey(Beer, on_delete=models.CASCADE)
	beer_name = models.CharField(max_length=250)
	point_value = models.IntegerField(default=1)
	total_drank = models.IntegerField("number of players who drank this beer")

	def __str__(self):
		return "{0}/{1}".format(self.beer.name, self.beer.brewery)

class Brewery_Manager(models.Manager):

	def create_brewery(self, name, untappd_id):
		return self.create(name=name, untappd_id=untappd_id)

class Brewery(models.Model):
	name = models.CharField(max_length=250)
	untappd_id = models.CharField(max_length=25, null=True, blank=True,)
	untappd_url = models.URLField(null=True, blank=True,)
	state = models.CharField(max_length=250)
	last_updated = models.DateTimeField()

	objects = Brewery_Manager()

class Contest_BreweryManager(models.Manager):

	def link(contest, brewery, value):
		return self.create(contest=contest, brewery=brewery,
			brewery_name=brewery.name, point_value=value, total_drank=0,)

class Contest_Brewery(models.Model):
	contest = models.ForeignKey(Contest, on_delete=models.CASCADE)
	brewery = models.ForeignKey(Brewery, on_delete=models.CASCADE)
	brewery_name = models.CharField(max_length=250)
	point_value = models.IntegerField(default=1)
	total_visited = models.IntegerField("number of players who drank at this brewery")

	objects = Contest_BreweryManager()

class Contest_PlayerManager(models.Manager):
	"""Manager for linking contests to players"""

	def link(self, contest, player):
		cp = self.create(contest=contest, player=player,
					user_name=player.user.username,
					beer_count=0,
					last_checkin_date=None,
					last_checkin_beer=None,
					last_checkin_load=contest.start_date,
					rank=-1)
		return cp

class Contest_Player(models.Model):
	""" Links a player's activities relative to a contest
		A reverse sort by contest and beer count gives you a leaderboard"""
	contest = models.ForeignKey(Contest, on_delete=models.CASCADE)
	player = models.ForeignKey(Player, on_delete=models.CASCADE)
	user_name = models.CharField(max_length=50)
	beer_count = models.IntegerField(default=0)
	beer_points = models.IntegerField(default=0)
	brewery_points = models.IntegerField(default=0)
	total_points = models.IntegerField(default=0)
	last_checkin_date = models.DateTimeField("Denormalized date from last checkin", null=True, blank=True)
	last_checkin_beer = models.CharField("Denormalized beer name from last checkin", null=True, max_length=250, blank=True)
	last_checkin_brewery  = models.CharField("Denormalized brewery name from last checkin", null=True, max_length=250, blank=True)
	last_checkin_load = models.DateTimeField("Latest date in the last load for this player")
	rank = models.IntegerField(default=0)

	objects = Contest_PlayerManager()

	def __str__(self):
		return "{0}:[Player={1}]".format(self.contest.name, self.user_name)

class Unvalidated_CheckinManager(models.Manager):
	def create_checkin(self, contest_player, untappd_title, brewery, beer,
						untappd_checkin, untappd_checkin_date):
		uv = self.create(contest_player=contest_player,
						untappd_title=untappd_title,
						brewery=brewery,
						beer=beer,
						untappd_checkin=untappd_checkin,
						untappd_checkin_date=untappd_checkin_date)
		return uv

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

class Contest_Checkin(models.Model):
	contest_player = models.ForeignKey(Contest_Player, on_delete=models.CASCADE)
	contest_beer = models.ForeignKey(Contest_Beer, on_delete=models.CASCADE, blank=True, null=True,)
	contest_brewery = models.ForeignKey(Contest_Brewery, on_delete=models.CASCADE, blank=True, null=True,)
	checkin_points = models.IntegerField(default=1)
	checkin_time = models.DateTimeField()
	untappd_checkin = models.URLField(max_length=250, null=True, blank=True)

	objects = Contest_CheckinManager()
