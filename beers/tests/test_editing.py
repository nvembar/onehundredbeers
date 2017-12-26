"""Tests the contest editing features and their models"""

import datetime
import json
from django.test import TestCase, override_settings, Client
from django.core.urlresolvers import reverse
from django.utils import timezone
from beers.models import Beer, Brewery, Contest, Contest_Player, \
                         Unvalidated_Checkin, Contest_Checkin, Contest_Beer, \
                         Contest_Brewery, Player

@override_settings(SECURE_SSL_REDIRECT=False, ROOTURL_CONF='beers.urls')
class ContestEditingTestCase(TestCase):
    """Tests the contest editing features"""

    fixtures = ['permissions', 'users']

    def test_successful_add_contest(self):
        """
        Tests whether a new contest can be added, requiring a new name and a 
        valid start and end date.
        """
        pass


    def test_not_runner_add_contest(self):
        """
        Tests whether there is a failure if a new contest is attempted to be
        added if a user is not a contest runner
        """
        pass


    def test_no_login_add_contest(self):
        """
        Tests whether there is a failure if a new contest is attempted to be
        added if a user is not logged in
        """
        pass


    def test_bad_contest_date_range_add_contest(self):
        """
        Tests whether the contests must end after the current date and have a
        start date before the current date.
        """
        pass


   def test_nonunique_contest_name_add_contest(self):
       """
       Tests whether the contest fails addition when a contest does not have a 
       unique name.
       """
       pass


   def test_successful_add_beer(self):
       """
       Tests whether a new beer can be added to a contest.
       """
       pass


   def test_not_contest_runner_add_beer(self):
       """
       Tests whether a non-contest runner is prevented from adding a beer.
       """
       pass


   def test_active_add_beer(self):
       """
       Tests whether a contest runner is prevented from adding a beer to an
       active contest.
       """
       pass


   def test_nonunique_add_beer(self):
       """
       Tests whether a beer fails to be added to a contest based on non-unique
       Untappd URLs
       """
       pass


   def test_successful_add_brewery(self):
       """
       Tests whether a brewery can successfully be added to a contest based.
       """
       pass


   def test_nonunique_add_brewery(self):
       """
       Tests whether a brewery fails to be added to a contest based on non-unique
       Untappd URLs
       """
       pass


   def test_active_add_brewery(self):
       """
       Tests whether a contest runner is prevented from adding a brewery to an
       active contest.
       """
       pass


   def test_not_contest_runner_add_beer(self):
       """
       Tests whether a non-contest runner is prevented from adding a beer.
       """
       pass


   def test_successful_add_challenge_by_runner(self):
       """
       Tests whether a contest runner can add a challenge
       """
       pass


   def test_successful_add_challenge_by_runner(self):
       """
       Tests whether a contest player can add a challenge
       """
       pass


   def test_active_add_challenge(self):
       """
       Tests whether a player or contest runner cannot add a challenge to an 
       active contest.
       """
       pass
