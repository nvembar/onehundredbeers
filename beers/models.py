from django.db import models
from django.contrib.auth.models import User

# The user profile.
class Player(models.Model):
	user = models.OneToOneField(User, on_delete=models.CASCADE)
	personal_statement = models.CharField(max_length=150, blank=True, default='')
	untappd_rss = models.URLField(max_length=512, null=True, blank=True)

	@classmethod
	def create(cls, user, personal_statement=None, untappd_rss=None):
		player = cls(user=user, personal_statement=personal_statement, untappd_rss=untappd_rss)
		return player

	def __str__(self):
		return self.user.username

# Create your models here.
class Beer(models.Model):
	name = models.CharField(max_length=250)
	brewery = models.CharField(max_length=250)
	style = models.CharField(max_length=250, null=True, blank=True, default='')
	brewery_lat = models.FloatField(null=True, blank=True)
	brewery_lon = models.FloatField(null=True, blank=True)
	untappd_id = models.CharField(max_length=25, null=True, blank=True)
	last_updated = models.DateTimeField()

	def __str__(self):
		return self.name


class Contest(models.Model):
	name = models.CharField(max_length=250)
	creator = models.ForeignKey(Player, default=1)
	active = models.BooleanField(default=False)
	created_on = models.DateTimeField()
	last_updated = models.DateTimeField()
	start_date = models.DateTimeField()
	end_date = models.DateTimeField()
	user_count = models.IntegerField(default=0)
	beer_count = models.IntegerField(default=0)

	def __str__(self):
		return self.name

class Contest_Beer(models.Model):
	contest = models.ForeignKey(Contest, on_delete=models.CASCADE)
	beer = models.ForeignKey(Beer, on_delete=models.CASCADE)
	beer_name = models.CharField(max_length=250)
	total_drank = models.IntegerField("number of players who drank this beer")

	def __str__(self):
		return "{0}: {1}".format(self.contest, self.beer_name)

# Links a player's activities relative to a contest
# A reverse sort by contest and beer count gives you a leaderboard
class Contest_Player(models.Model):
	contest = models.ForeignKey(Contest, on_delete=models.CASCADE)
	player = models.ForeignKey(Player, on_delete=models.CASCADE)
	user_name = models.CharField(max_length=50)
	beer_count = models.IntegerField(default=0)
	last_checkin_date = models.DateTimeField("Denormalized date from last checkin", null=True, blank=True)
	last_checkin_beer = models.CharField("Denormalized beer name from last checkin", null=True, max_length=250, blank=True)
	rank = models.IntegerField(default=0)

	def __str__(self):
		return "{0}:[Player={1}]".format(self.contest.name, self.user_name)

class Checkin(models.Model):
	player = models.ForeignKey(Player, on_delete=models.CASCADE)
	beer = models.ForeignKey(Beer, on_delete=models.CASCADE)
	checkin_time = models.DateTimeField()
	comment = models.CharField(max_length=250, null=True, blank=True, default='')
	rating = models.IntegerField(default=-1)
	untappd_checkin = models.URLField(max_length=250, null=True, blank=True)
