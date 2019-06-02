"""Captures all the Contest association classes between contests and the 
   drinks and bonuses"""

import logging
from django.contrib.postgres.fields import ArrayField
from django.db import models
from .drinks import Beer, Brewery

logger = logging.getLogger(__name__)

class Contest_BreweryManager(models.Manager):

    def link(self, contest, brewery, value):
        return self.create(contest=contest, brewery=brewery,
                           brewery_name=brewery.name,
                           point_value=value, total_drank=0,)

class Contest_Brewery(models.Model):
    from .contest import Contest
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE)
    brewery = models.ForeignKey(Brewery, on_delete=models.CASCADE)
    brewery_name = models.CharField(max_length=250)
    point_value = models.IntegerField(default=1)
    total_visited = models.IntegerField(default=0, 
			help_text="number of players who drank at this brewery")

    objects = Contest_BreweryManager()

    def __str__(self):
        return '{}/{}'.format(self.contest.name, self.brewery.name)


class Contest_Beer(models.Model):
    "Represents a many-to-many connection between a beer and a contest"

    from .contest import Contest
    from .contest_player import Contest_Player
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE)
    challenger = models.ForeignKey(Contest_Player,
                                   on_delete=models.CASCADE,
                                   default=None,
                                   null=True,
                                  )
    beer = models.ForeignKey(Beer, on_delete=models.CASCADE)
    beer_name = models.CharField(max_length=250)
    brewery_name = models.CharField(max_length=250, default='')
    point_value = models.IntegerField(default=1)
    challenge_point_loss = models.IntegerField(default=0)
    max_point_loss = models.IntegerField(default=0)
    challenge_point_value = models.IntegerField(
        default=0,
        help_text='The number of points the challenger gets ' +
            'for drinking this beer')
    total_drank = models.IntegerField("number of players who drank this beer")

    class Meta:
        unique_together = (('contest', 'beer'),)

    def __str__(self):
        return "{0}/{1}".format(self.beer.name, self.beer.brewery)

class Contest_Bonus(models.Model):
    """Represents a bonus associated with a particular contest"""
    from .contest import Contest

    contest = models.ForeignKey(Contest, on_delete=models.CASCADE)
    name = models.CharField(max_length=50, default=None, null=False, blank=False,)
    description = models.CharField(max_length=250, default="", null=True, blank=True,)
    hashtags = ArrayField(base_field=models.CharField(max_length=30, default=None),
                          null=True, 
                          default=None)
    point_value = models.IntegerField(default=1,)

    class Meta:
        unique_together = (('contest', 'name'),)