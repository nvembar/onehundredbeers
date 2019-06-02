"""Object representing the unvalidated checkin"""
import datetime
import logging
from django.contrib.postgres.fields import ArrayField
from django.db import models

logger = logging.getLogger(__name__)

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
    from beers.models.models import Contest_Player
    contest_player = models.ForeignKey(Contest_Player, on_delete=models.CASCADE)
    untappd_title = models.CharField(max_length=500, blank=False)
    untappd_checkin = models.URLField()
    untappd_checkin_date = models.DateTimeField()
    brewery = models.CharField(max_length=250, default='')
    beer = models.CharField(max_length=250, default='')
    beer_url = models.URLField(null=True, default=None)
    brewery_url = models.URLField(null=True, default=None)
    possible_bonuses = ArrayField(base_field=models.IntegerField(), 
                                  null=True, 
                                  default=None)
    has_possibles = models.BooleanField(default=False)
    photo_url = models.URLField(null=True, default=None)
    rating = models.IntegerField(null=True, default=None)

    objects = Unvalidated_CheckinManager()

    def __str__(self):
        return """Checkin[beer={},
                       brewery={},
                       beer_url={},
                       brewery_url={},
                       checkin_url={},
                       time={},
                       photo_url={}]""".format(self.beer, 
                                              self.brewery,
                                              self.beer_url,
                                              self.brewery_url,
                                              self.untappd_checkin,
                                              self.untappd_checkin_date.isoformat(),
                                              self.photo_url)