"""Implements the player objects"""

import logging
from django.db import models
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)

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
