from django.test import TestCase, TransactionTestCase, override_settings
from django.test import Client
from django.contrib.auth.models import User, Group, Permission
from django.core.urlresolvers import reverse
from beers.models import Contest, Player, Contest_Player, Unvalidated_Checkin, Contest_Checkin, Brewery, Contest_Brewery
from django.utils import timezone
from beers.utils.checkin import checkin_brewery
import datetime
import json

@override_settings(SECURE_SSL_REDIRECT=False, ROOTURL_CONF='beers.urls')
class BreweryTestCase(TestCase):

    fixtures = [ 'permissions', 'users', 'contest_tests', 'unvalidated_checkins']

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_successful_util_checkin_with_delete(self):
        """
        Tests whether the utility for checking in a brewery works correctly
        """
        uv = Unvalidated_Checkin.objects.get(brewery='Brewery 2')
        uv_id = uv.id
        uv_url = uv.untappd_checkin
        uv_date = uv.untappd_checkin_date
        cp = Contest_Player.objects.get(contest__id=1, user_name='user1')
        total_points = cp.total_points
        beer_points = cp.beer_points
        brewery_points = cp.brewery_points
        cb = Contest_Brewery.objects.get(contest=cp.contest, brewery_name='Brewery 2')
        checkin = checkin_brewery(uv, cb)
        self.assertIsNotNone(checkin)
        self.assertEqual(checkin.contest_brewery, cb)
        self.assertIsNone(checkin.contest_beer)
        with self.assertRaises(Unvalidated_Checkin.DoesNotExist):
            Unvalidated_Checkin.objects.get(id=uv_id)
        cp_update = Contest_Player.objects.get(contest__id=1, user_name='user1')
        self.assertEqual(beer_points, cp_update.beer_points)
        self.assertEqual(brewery_points + cb.point_value, cp_update.brewery_points)
        self.assertEqual(total_points + cb.point_value, cp_update.total_points)
        self.assertEqual(cb.brewery_name, cp_update.last_checkin_brewery)
        self.assertEqual(cp_update.last_checkin_date, uv_date)

    def test_successful_util_checkin_without_delete(self):
        """
        Tests whether the utility for checking in a brewery works correctly
        when save_checkin is passed
        """
        uv = Unvalidated_Checkin.objects.get(brewery='Brewery 2')
        uv_id = uv.id
        uv_url = uv.untappd_checkin
        cp = Contest_Player.objects.get(contest__id=1, user_name='user1')
        total_points = cp.total_points
        beer_points = cp.beer_points
        brewery_points = cp.brewery_points
        cb = Contest_Brewery.objects.get(contest=cp.contest, brewery_name='Brewery 2')
        checkin = checkin_brewery(uv, cb, save_checkin=True)
        self.assertIsNotNone(checkin)
        self.assertEqual(checkin.contest_brewery, cb)
        self.assertIsNone(checkin.contest_beer)
        uv_update = Unvalidated_Checkin.objects.get(id=uv_id)
        self.assertIsNotNone(uv_update)
        cp_update = Contest_Player.objects.get(contest__id=1, user_name='user1')
        self.assertEqual(beer_points, cp_update.beer_points)
        self.assertEqual(brewery_points + cb.point_value, cp_update.brewery_points)
        self.assertEqual(total_points + cb.point_value, cp_update.total_points)
        self.assertEqual(cb.brewery_name, cp_update.last_checkin_brewery)
        self.assertEqual(cp_update.last_checkin_date, uv_date)

    def test_redundant_checkin(self):
        """
        Once a user has checked into a brewery, they shouldn't be able to
        check into it again
        """
        # The fixture has two Brewery 1 checkins
        uvs = Unvalidated_Checkin.objects.filter(brewery='Brewery 1')
        uv = uvs[0]
        uv_id = uv.id
        uv_url = uv.untappd_checkin
        cp = Contest_Player.objects.get(contest__id=1, user_name='user1')
        total_points = cp.total_points
        beer_points = cp.beer_points
        brewery_points = cp.brewery_points
        cb = Contest_Brewery.objects.get(contest=cp.contest, brewery_name='Brewery 1')
        checkin = checkin_brewery(uv, cb)
        self.assertIsNotNone(checkin)
        self.assertEqual(checkin.contest_brewery, cb)
        self.assertIsNone(checkin.contest_beer)
        checkin_id = checkin.id
        uv_update = Unvalidated_Checkin.objects.get(id=uv_id)
        self.assertIsNotNone(uv_update)
        cp_update = Contest_Player.objects.get(contest__id=1, user_name='user1')
        self.assertEqual(beer_points, cp_update.beer_points)
        self.assertEqual(brewery_points + cb.point_value, cp_update.brewery_points)
        self.assertEqual(total_points + cb.point_value, cp_update.total_points)
        self.assertEqual(cb.brewery_name, cp_update.last_checkin_brewery)
        redundant_uv = uvs[1]
        redundant_uv_date = redundant_uv.untappd_checkin_date
        second_checkin = checkin_brewery(redundant_uv, cb)
        assertIsNone(redundant_uv)
        cp_update = Contest_Player.objects.get(contest__id=1, user_name='user1')
        self.assertEqual(beer_points, cp_update.beer_points)
        self.assertEqual(brewery_points + cb.point_value, cp_update.brewery_points)
        self.assertEqual(total_points + cb.point_value, cp_update.total_points)
        self.assertEqual(cb.brewery_name, cp_update.last_checkin_brewery)
        self.assertEqual(cp_update.last_checkin_date, redundant_uv_date)
