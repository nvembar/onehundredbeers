"""The objects that can get a player points"""
import datetime
import logging
from django.db import models
from django.utils import timezone


class BeerManager(models.Manager):
    """Manages beer data"""
    def create_beer(self, name, brewery, untappd_url='',
                    style='', description='', brewery_url='',
                    brewery_city='', brewery_state=''):
        """Creates a contest with defaults on active status, creation date,
        update date, beer count, and user count"""
        beer = self.create(name=name, brewery=brewery,
                           style=style, description=description,
                           untappd_url=untappd_url,
                           brewery_city=brewery_city,
                           brewery_state=brewery_state,
                           brewery_url=brewery_url,
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
    untappd_url = models.URLField(null=True, blank=True)
    brewery_url = models.URLField(null=True, blank=True)
    last_updated = models.DateTimeField()

    objects = BeerManager()

    def __str__(self):
        return "Beer[{}<{}> / {}<{}>]".format(self.name, 
                                        self.untappd_url, 
                                        self.brewery, self.brewery_url)


class Brewery_Manager(models.Manager):

    def create_brewery(self, name, untappd_url, location=None,):
        return self.create(name=name, 
                           untappd_url=untappd_url,
                           location=location,
						   last_updated=timezone.now())

class Brewery(models.Model):
    name = models.CharField(max_length=250)
    untappd_id = models.CharField(max_length=25, null=True, blank=True,)
    untappd_url = models.URLField(null=True, blank=True,)
    state = models.CharField(max_length=250)
    location = models.CharField(max_length=250, null=True, blank=True, default=None)
    last_updated = models.DateTimeField()

    objects = Brewery_Manager()

    def __str__(self):
        return "Brewery[name={}, url={}, location={}]".format(self.name,
                                                              self.untappd_url,
                                                              self.location)