from django.test import TestCase, override_settings
from django.test import Client
from django.contrib.auth.models import User, Group, Permission
from beers.models import Contest_Beer, Beer, Contest, Player, Contest_Player, Unvalidated_Checkin
from beers.utils.loader import create_contest_from_csv
from beers.utils.checkin import load_player_checkins
from hundred_beers.settings import BASE_DIR
import datetime
from django.utils import timezone
import io
import os
import feedparser
from unittest.mock import patch

override_settings(SECURE_SSL_REDIRECT=False, ROOTURL_CONF='beers.urls')
class LoaderTestCase(TestCase):

    fixtures = [ 'permissions', 'users' ]

    WELL_FORMED_CSV = """Brewery,Beer,URL,State,Points
Brewery 1,Beer 1,https://example.com/untapped1,ST,1
Brewery 2,Beer 2,https://example.com/untapped2,ST,1
Brewery 3,Beer 3,https://example.com/untapped3,ST,1
Brewery 4,Beer 4,https://example.com/untapped4,ST,3
Brewery 5,Beer 5,https://example.com/untapped4,ST,3
"""

    BADLY_FORMED_CSV = """Brewery,Beer,URL,State,Points
Brewery 1,Beer 1,https://example.com/untapped1,ST,1
Brewery 2,Beer 2,https://example.com/untapped2,ST,not points
Brewery 3,Beer 3,https://example.com/untapped3,ST,1
Brewery 4,Beer 4,https://example.com/untapped4,ST,3
Brewery 5,Beer 5,https://example.com/untapped4,ST,3
"""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_successful_load(self):
        stream = io.StringIO(LoaderTestCase.WELL_FORMED_CSV)
        runner = Player.objects.get(id=4)
        start_date = timezone.make_aware(datetime.datetime(2017, 1, 1))
        end_date = timezone.make_aware(datetime.datetime(2017, 12, 31))
        create_contest_from_csv(name='Contest', runner=runner,
                start_date=start_date,
                end_date=end_date,
                stream=stream,)
        contest = Contest.objects.get(name='Contest')
        self.assertEqual(contest.creator.id, runner.id)
        self.assertEqual(Beer.objects.all().count(), 5)
        self.assertEqual(Beer.objects.get(name='Beer 1').brewery, 'Brewery 1')
        beers = Contest_Beer.objects.filter(contest__id=contest.id)
        self.assertEqual(beers.count(), 5)
        self.assertEqual(beers.filter(beer_name='Beer 1').count(), 1)
        self.assertEqual(beers.filter(beer_name='Beer 1').get().point_value, 1)
        self.assertEqual(beers.filter(beer_name='Beer 2').count(), 1)
        self.assertEqual(beers.filter(beer_name='Beer 2').get().point_value, 1)
        self.assertEqual(beers.filter(beer_name='Beer 3').count(), 1)
        self.assertEqual(beers.filter(beer_name='Beer 3').get().point_value, 1)
        self.assertEqual(beers.filter(beer_name='Beer 4').count(), 1)
        self.assertEqual(beers.filter(beer_name='Beer 4').get().point_value, 3)
        self.assertEqual(beers.filter(beer_name='Beer 5').count(), 1)
        self.assertEqual(beers.filter(beer_name='Beer 5').get().point_value, 3)

    def test_bad_csv(self):
        stream = io.StringIO(LoaderTestCase.BADLY_FORMED_CSV)
        runner = Player.objects.get(id=4)
        start_date = timezone.make_aware(datetime.datetime(2017, 1, 1))
        end_date = timezone.make_aware(datetime.datetime(2017, 12, 31))
        with self.assertRaises(ValueError):
            create_contest_from_csv(name='Contest', runner=runner,
                    start_date=start_date,
                    end_date=end_date,
                    stream=stream,)

    def test_successful_feed(self):
        runner = Player.objects.get(id=4)
        player = Player.objects.get(id=1)
        player.untappd_rss = os.path.join(BASE_DIR, '..', 'test-data', 'test-checkins.xml')
        player.save()
        contest = Contest.objects.create_contest('Contest', runner,
                timezone.make_aware(datetime.datetime(2017, 1, 1)),
                timezone.make_aware(datetime.datetime(2017, 12, 31)))
        contest.save()
        cp = Contest_Player.objects.link(contest, player)
        cp.save()
        load_player_checkins(player)
        self.assertEqual(Unvalidated_Checkin.objects.filter(contest_player=cp).count(), 25)
