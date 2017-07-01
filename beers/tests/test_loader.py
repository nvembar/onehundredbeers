import datetime
import io
import os
from django.test import TestCase, override_settings
from django.utils import timezone
from django.core.management import call_command
from django.core.management.base import CommandError
from beers.models import Contest_Beer, Beer, Contest, Player, Unvalidated_Checkin
from beers.utils.loader import create_contest_from_csv
from beers.utils.checkin import load_player_checkins
from hundred_beers.settings import BASE_DIR
from unittest.mock import patch


@override_settings(SECURE_SSL_REDIRECT=False, ROOTURL_CONF='beers.urls')
class LoaderTestCase(TestCase):
    """Tests the loader functions and commands"""

    fixtures = ['permissions', 'users']

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
        """Tests a successful load of a contest from a CSV"""
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
        """Tests whether the loader fails correctly with a bad CSV"""
        stream = io.StringIO(LoaderTestCase.BADLY_FORMED_CSV)
        runner = Player.objects.get(id=4)
        start_date = timezone.make_aware(datetime.datetime(2017, 1, 1))
        end_date = timezone.make_aware(datetime.datetime(2017, 12, 31))
        with self.assertRaises(ValueError):
            create_contest_from_csv(name='Contest', runner=runner,
                                    start_date=start_date,
                                    end_date=end_date,
                                    stream=stream,)


    def test_successful_feed_for_player(self):
        """Test the ability to load a single XML feed file for a user"""
        runner = Player.objects.get(id=4)
        player = Player.objects.get(id=1)
        player.untappd_rss = os.path.join(BASE_DIR, '..', 'test-data', 'test-checkins.xml')
        player.save()
        contest = Contest.objects.create_contest('Contest', runner,
            timezone.make_aware(datetime.datetime(2017, 1, 1)),
            timezone.make_aware(datetime.datetime(2017, 12, 31)))
        contest.save()
        cp = contest.add_player(player)
        cp.save()
        load_player_checkins(player)
        self.assertEqual(Unvalidated_Checkin.objects.filter(contest_player=cp).count(), 25)

    def test_successful_feed_for_player_twice(self):
        """
        Test the ability to load a single XML feed file for a user twice.
        The second call shouldn't add any new checkins because they'd be
        redundant
        """
        runner = Player.objects.get(id=4)
        player = Player.objects.get(id=1)
        player.untappd_rss = os.path.join(BASE_DIR, '..', 'test-data', 'test-checkins.xml')
        player.save()
        contest = Contest.objects.create_contest('Contest', runner,
            timezone.make_aware(datetime.datetime(2017, 1, 1)),
            timezone.make_aware(datetime.datetime(2017, 12, 31)))
        contest.save()
        cp = contest.add_player(player)
        cp.save()
        load_player_checkins(player)
        self.assertEqual(Unvalidated_Checkin.objects.filter(contest_player=cp).count(), 25)
        load_player_checkins(player)
        self.assertEqual(Unvalidated_Checkin.objects.filter(contest_player=cp).count(), 25)

    def test_successful_feed_after_date(self):
        """Tests the ability to load a subset of a XML feed after a certain date"""
        runner = Player.objects.get(id=4)
        player = Player.objects.get(id=1)
        player.untappd_rss = os.path.join(BASE_DIR, '..', 'test-data', 'test-checkins.xml')
        player.save()
        contest = Contest.objects.create_contest('Contest', runner,
            timezone.make_aware(datetime.datetime(2017, 1, 1)),
            timezone.make_aware(datetime.datetime(2017, 12, 31)))
        contest.save()
        cp = contest.add_player(player)
        cp.save()
        from_date = timezone.make_aware(datetime.datetime(2017, 6, 1))
        load_player_checkins(player, from_date=from_date)
        self.assertEqual(Unvalidated_Checkin.objects.filter(contest_player=cp).count(), 4)

    def test_successful_checkin_command_for_player(self):
        """Tests whether the checkin command works for a single player"""
        runner = Player.objects.get(id=4)
        player = Player.objects.get(id=1)
        player.untappd_rss = os.path.join(BASE_DIR, '..', 'test-data', 'test-checkins.xml')
        player.save()
        contest = Contest.objects.create_contest('Contest', runner,
            timezone.make_aware(datetime.datetime(2017, 1, 1)),
            timezone.make_aware(datetime.datetime(2017, 12, 31)))
        contest.save()
        cp = contest.add_player(player)
        cp.save()
        call_command('load-checkins', '--player', player.user.username)
        self.assertEqual(Unvalidated_Checkin.objects.filter(contest_player=cp).count(), 25)

    def test_successful_checkin_command_for_player_after_date(self):
        """Test the ability to load a single XML feed file for a user"""
        runner = Player.objects.get(id=4)
        player = Player.objects.get(id=1)
        player.untappd_rss = os.path.join(BASE_DIR, '..', 'test-data', 'test-checkins.xml')
        player.save()
        contest = Contest.objects.create_contest('Contest', runner,
            timezone.make_aware(datetime.datetime(2017, 1, 1)),
            timezone.make_aware(datetime.datetime(2017, 12, 31)))
        contest.save()
        cp = contest.add_player(player)
        cp.save()
        call_command('load-checkins', '--after-date', '2017-06-01')
        self.assertEqual(Unvalidated_Checkin.objects.all().count(), 4)

    def test_successful_checkin_command_for_all(self):
        """Test the ability to load a single XML feed file for a user"""
        runner = Player.objects.get(id=4)
        runner.untappd_rss = os.path.join(BASE_DIR, '..', 'test-data', 'test-checkins.xml')
        runner.save()
        player = Player.objects.get(id=1)
        player.untappd_rss = os.path.join(BASE_DIR, '..', 'test-data', 'test-checkins.xml')
        player.save()
        contest = Contest.objects.create_contest('Contest', runner,
            timezone.make_aware(datetime.datetime(2017, 1, 1)),
            timezone.make_aware(datetime.datetime(2017, 12, 31)))
        contest.save()
        cp = contest.add_player(player)
        cp.save()
        cp = contest.add_player(runner)
        cp.save()
        call_command('load-checkins')
        self.assertEqual(Unvalidated_Checkin.objects.all().count(), 50)

    def test_successful_checkin_command_for_all_after_date(self):
        """Test the ability to load a single XML feed file for a user"""
        runner = Player.objects.get(id=4)
        runner.untappd_rss = os.path.join(BASE_DIR, '..', 'test-data', 'test-checkins.xml')
        runner.save()
        player = Player.objects.get(id=1)
        player.untappd_rss = os.path.join(BASE_DIR, '..', 'test-data', 'test-checkins.xml')
        player.save()
        contest = Contest.objects.create_contest('Contest', runner,
            timezone.make_aware(datetime.datetime(2017, 1, 1)),
            timezone.make_aware(datetime.datetime(2017, 12, 31)))
        contest.save()
        cp = contest.add_player(player)
        cp.save()
        cp = contest.add_player(runner)
        cp.save()
        call_command('load-checkins', '--after-date', '2017-06-01')
        self.assertEqual(Unvalidated_Checkin.objects.all().count(), 8)

    def test_unsucessful_checkin_command_with_bad_contest(self):
        """Test whether a checkin command with bad contest arguments fails"""
        with self.assertRaises(CommandError):
            call_command('load-checkins', '--contest', 'bad bad')
        with self.assertRaises(CommandError):
            call_command('load-checkins', '--contest', 1000)


    def test_unsucessful_checkin_command_with_bad_player(self):
        """Test whether a checkin command with bad player argument fails"""
        with self.assertRaises(CommandError):
            call_command('load-checkins', '--player', 'no such player')

    def test_unsucessful_checkin_command_with_bad_after_date(self):
        """Test whether a checkin command with bad date argument fails"""
        with self.assertRaises(CommandError):
            call_command('load-checkins', '--after-date', 'is not a date')
