"""
Tests the loader utilities and commands for the hundred beers app
"""

import datetime
import io
import tempfile
import os
import re
import uuid
import json
from string import Template
from unittest.mock import patch, MagicMock
from unittest import skip
import boto3
import botocore.session
from botocore.stub import Stubber
from django.test import TestCase, override_settings
from django.utils import timezone
from django.core.management import call_command
from django.core.management.base import CommandError
from beers.models import Contest_Beer, Beer, Contest, User, Player, \
                         Contest_Checkin, Unvalidated_Checkin, Contest_Bonus
from beers.utils.loader import create_contest_from_csv
from beers.utils.checkin import load_player_checkins
from hundred_beers.settings import BASE_DIR

FAKE_ARN = 'this_is_a_long_fake_arn'


def sts_boto_patch(client_type):
    "A patch for the boto.client('sts') call made in new_contest"
    if client_type == 'sts':
        sts = botocore.session.get_session().create_client('sts')
        stub = Stubber(sts)
        response = {'Credentials':
                        {'AccessKeyId': 'access_key_id_string',
                         'SecretAccessKey': 'secret_access_string',
                         'SessionToken': 'session_string',
                         'Expiration': datetime.datetime.now(),
                        },
                    'AssumedRoleUser':
                        {'AssumedRoleId': 'assumed_role_id_string_get_long',
                         'Arn': 'arn_string_this_needs_to_be_long',
                        },
                    'PackedPolicySize': 123,
                   }
        expected = {'RoleArn': FAKE_ARN,
                    'RoleSessionName': 'LoadContest'}
        stub.add_response('assume_role', response, expected)
        stub.activate()
        return sts
    else:
        raise ValueError('Expected "sts" as the patched boto client')


def s3_boto_well_formed_patch(client_type,
                              aws_access_key_id='access_key_id',
                              aws_secret_access_key='secret_access_key',
                              aws_session_token='session_token'):
    """Patch for boto3.resource"""
    def _download_file(stream):
        """Stubs out the download_fileobj S3 object call"""
        stream.write(LoaderTestCase.WELL_FORMED_CSV.encode('ascii'))
    mock = MagicMock()
    mock.Object.return_value.download_fileobj.side_effect = _download_file
    return mock

def s3_boto_badly_formed_patch(client_type,
                               aws_access_key_id='access_key_id',
                               aws_secret_access_key='secret_access_key',
                               aws_session_token='session_token'):
    """Patch for boto3.resource"""
    def _download_file(stream):
        """Stubs out the download_fileobj S3 object call"""
        stream.write(LoaderTestCase.BADLY_FORMED_CSV.encode('ascii'))
    mock = MagicMock()
    mock.Object.return_value.download_fileobj.side_effect = _download_file
    return mock


@override_settings(SECURE_SSL_REDIRECT=False,
                   ROOTURL_CONF='beers.urls',
                   LOADER_ROLE_ARN=FAKE_ARN)
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

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        rss_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'test-data', 'test-checkins.xml')
        updated_rss_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'test-data', 'test-checkins.adjusted.xml')
        

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

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

    @patch.object(boto3, 'client', new=sts_boto_patch)
    @patch.object(boto3, 'resource', new=s3_boto_well_formed_patch)
    def test_successful_new_contest_command(self):
        """Tests whether the new context command works"""
        runner = Player.objects.get(id=4)
        call_command('new_contest',
                     'Contest',
                     runner.user.username,
                     '01-01-2017',
                     '12-31-2017',
                     'bucket',
                     'well-formed')
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

    @patch.object(boto3, 'client', new=sts_boto_patch)
    @patch.object(boto3, 'resource', new=s3_boto_badly_formed_patch)
    def test_unsuccessful_new_contest_command(self):
        """Tests whether the new context command fails on bad input"""
        runner = Player.objects.get(id=4)
        with self.assertRaises(ValueError):
            call_command('new_contest',
                         'Contest',
                         runner.user.username,
                         '01-01-2017',
                         '12-31-2017',
                         'bucket',
                         'badly-formed')

    @skip("This was calling out to Untappd")
    def test_successful_feed_for_player(self):
        """Test the ability to load a single XML feed file for a user"""
        runner = Player.objects.get(id=4)
        player = Player.objects.get(id=1)
        player.untappd_rss = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'test-data', 'test-checkins.xml')
        start_date = timezone.make_aware(datetime.datetime(2017, 1, 1))
        end_date = timezone.make_aware(datetime.datetime(2017, 12, 31))
        contest = Contest.objects.create_contest('Contest',
                                                 runner,
                                                 start_date,
                                                 end_date)
        contest.save()
        contest_player = contest.add_player(player)
        contest_player.save()
        load_player_checkins(player)
        checkins = Unvalidated_Checkin.objects.filter(contest_player=contest_player)
        self.assertEqual(checkins.count(), 25)

    @skip("This was calling out to Untappd")
    def test_successful_feed_for_player_twice(self):
        """
        Test the ability to load a single XML feed file for a user twice.
        The second call shouldn't add any new checkins because they'd be
        redundant
        """
        runner = Player.objects.get(id=4)
        player = Player.objects.get(id=1)
        player.untappd_rss = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'test-data', 'test-checkins.xml')
        player.save()
        start_date = timezone.make_aware(datetime.datetime(2017, 1, 1))
        end_date = timezone.make_aware(datetime.datetime(2017, 12, 31))
        contest = Contest.objects.create_contest('Contest',
                                                 runner,
                                                 start_date,
                                                 end_date)
        contest.save()
        contest_player = contest.add_player(player)
        contest_player.save()
        load_player_checkins(player)
        checkins = Unvalidated_Checkin.objects.filter(contest_player=contest_player)
        self.assertEqual(checkins.count(), 25)
        load_player_checkins(player)
        checkins = Unvalidated_Checkin.objects.filter(contest_player=contest_player)
        self.assertEqual(checkins.count(), 25)

    @skip("This was calling out to Untappd")
    def test_successful_feed_after_date(self):
        """Tests the ability to load a subset of a XML feed after a certain date"""
        runner = Player.objects.get(id=4)
        player = Player.objects.get(id=1)
        player.untappd_rss = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'test-data', 'test-checkins.xml')
        player.save()
        start_date = timezone.make_aware(datetime.datetime(2017, 1, 1))
        end_date = timezone.make_aware(datetime.datetime(2017, 12, 31))
        contest = Contest.objects.create_contest('Contest',
                                                 runner,
                                                 start_date,
                                                 end_date)
        contest.save()
        contest_player = contest.add_player(player)
        contest_player.save()
        from_date = timezone.make_aware(datetime.datetime(2017, 6, 1))
        load_player_checkins(player, from_date=from_date)
        checkins = Unvalidated_Checkin.objects.filter(contest_player=contest_player)
        self.assertEqual(checkins.count(), 4)

    @skip("This was calling out to Untappd")
    def test_successful_checkin_command_for_player(self):
        """Tests whether the checkin command works for a single player"""
        runner = Player.objects.get(id=4)
        player = Player.objects.get(id=1)
        player.untappd_rss = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'test-data', 'test-checkins.xml')
        player.save()
        start_date = timezone.make_aware(datetime.datetime(2017, 1, 1))
        end_date = timezone.make_aware(datetime.datetime(2017, 12, 31))
        contest = Contest.objects.create_contest('Contest',
                                                 runner,
                                                 start_date,
                                                 end_date)
        contest.save()
        contest_player = contest.add_player(player)
        contest_player.save()
        call_command('load_checkins', '--player', player.user.username)
        checkins = Unvalidated_Checkin.objects.filter(contest_player=contest_player)
        self.assertEqual(checkins.count(), 25)

    @skip("This was calling out to Untappd")
    def test_successful_checkin_command_for_player_after_date(self):
        """Test the ability to load a single XML feed file for a user"""
        runner = Player.objects.get(id=4)
        player = Player.objects.get(id=1)

        player.untappd_rss = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'test-data', 'test-checkins.xml')
        player.save()
        start_date = timezone.make_aware(datetime.datetime(2017, 1, 1))
        end_date = timezone.make_aware(datetime.datetime(2017, 12, 31))
        contest = Contest.objects.create_contest('Contest',
                                                 runner,
                                                 start_date,
                                                 end_date)
        contest.save()
        contest_player = contest.add_player(player)
        contest_player.save()
        call_command('load_checkins', '--after-date', '2017-06-01')
        self.assertEqual(Unvalidated_Checkin.objects.all().count(), 4)

    @skip("This was calling out to Untappd")
    def test_successful_checkin_command_for_all(self):
        """Test the ability to load all the XML feeds"""
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            'test-data', 'test-checkins.xml')
        start_date = timezone.make_aware(datetime.datetime(2017, 1, 1))
        end_date = timezone.make_aware(datetime.datetime(2017, 12, 31))
        runner = Player.objects.get(id=4)
        runner.untappd_rss = path
        runner.save()
        player = Player.objects.get(id=1)
        player.untappd_rss = path
        player.save()
        contest = Contest.objects.create_contest('Contest',
                                                 runner,
                                                 start_date,
                                                 end_date)
        contest.save()
        contest_player = contest.add_player(player)
        contest_player.save()
        contest_runner = contest.creator
        call_command('load_checkins')
        self.assertEqual(Unvalidated_Checkin.objects.all().count(), 50)

    @skip("This was calling out to Untappd")
    def test_successful_checkin_command_for_all_after_date(self):
        """Test the ability to load a single XML feed file for a user"""
        runner = Player.objects.get(id=4)
        runner.untappd_rss = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'test-data', 'test-checkins.xml')
        runner.save()
        player = Player.objects.get(id=1)
        player.untappd_rss = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'test-data', 'test-checkins.xml')
        player.save()
        start_date = timezone.make_aware(datetime.datetime(2017, 1, 1))
        end_date = timezone.make_aware(datetime.datetime(2017, 12, 31))
        contest = Contest.objects.create_contest('Contest',
                                                 runner,
                                                 start_date,
                                                 end_date)
        contest.save()
        contest_player = contest.add_player(player)
        contest_player.save()
        contest_runner = contest.creator
        call_command('load_checkins', '--after-date', '2017-06-01')
        self.assertEqual(Unvalidated_Checkin.objects.all().count(), 8)

    @skip("This was calling out to Untappd")
    def test_unsucessful_checkin_command_with_bad_contest(self):
        """Test whether a checkin command with bad contest arguments fails"""
        with self.assertRaises(CommandError):
            call_command('load_checkins', '--contest', 'bad bad')
        with self.assertRaises(CommandError):
            call_command('load_checkins', '--contest', 1000)

    @skip("This was calling out to Untappd")
    def test_unsucessful_checkin_command_with_bad_player(self):
        """Test whether a checkin command with bad player argument fails"""
        with self.assertRaises(CommandError):
            call_command('load_checkins', '--player', 'no such player')

    @skip("This was calling out to Untappd")
    def test_unsucessful_checkin_command_with_bad_after_date(self):
        """Test whether a checkin command with bad date argument fails"""
        with self.assertRaises(CommandError):
            call_command('load_checkins', '--after-date', 'is not a date')

    def test_successful_reload_checkin(self):
        """Test whether the reload_checkin command works"""
        runner = Player.objects.get(id=4)
        player = Player.objects.get(id=1)
        player.save()
        start_date = timezone.make_aware(datetime.datetime(2017, 1, 1))
        end_date = timezone.make_aware(datetime.datetime(2017, 12, 31))
        contest = Contest.objects.create_contest('Contest',
                                                 runner,
                                                 start_date,
                                                 end_date)
        contest.save()
        contest_player = contest.add_player(player)
        contest_player.save()
        beer = Beer.objects.create_beer('Reloaded Beer', 'Reloaded Brewery')
        contest_beer = contest.add_beer(beer)
        call_command('reload_checkin',
                     str(contest.id),
                     'https://example.com/checkin/1',
                     '6-1-2017',
                     contest_player.user_name,
                     'Reloaded Beer',
                     'Reloaded Brewery',)
        checkin = Contest_Checkin.objects.get(contest_player=contest_player,
                                              contest_beer=contest_beer)
        self.assertIsNotNone(checkin)
        self.assertEqual(checkin.checkin_time,
                         timezone.make_aware(datetime.datetime(2017, 6, 1)))
        contest_player.refresh_from_db()
        self.assertEqual(contest_player.beer_points, 1)
        self.assertEqual(contest_player.total_points, 1)

    def test_bad_date_reload_checkin(self):
        """Test whether the reload_checkin command fails on bad date input"""
        runner = Player.objects.get(id=4)
        player = Player.objects.get(id=1)
        player.save()
        start_date = timezone.make_aware(datetime.datetime(2017, 1, 1))
        end_date = timezone.make_aware(datetime.datetime(2017, 12, 31))
        contest = Contest.objects.create_contest('Contest',
                                                 runner,
                                                 start_date,
                                                 end_date)
        contest.save()
        contest_player = contest.add_player(player)
        contest_player.save()
        beer = Beer.objects.create_beer('Reloaded Beer', 'Reloaded Brewery')
        contest_beer = contest.add_beer(beer)
        with self.assertRaises(CommandError):
            call_command('reload_checkin',
                         str(contest.id),
                         'https://example.com/checkin/1',
                         'not a date',
                         contest_player.user_name,
                         'Reloaded Beer',
                         'Reloaded Brewery',)

    def test_bad_contest_reload_checkin(self):
        """Test whether the reload_checkin command fails on bad contest
        input"""
        runner = Player.objects.get(id=4)
        player = Player.objects.get(id=1)
        player.save()
        start_date = timezone.make_aware(datetime.datetime(2017, 1, 1))
        end_date = timezone.make_aware(datetime.datetime(2017, 12, 31))
        contest = Contest.objects.create_contest('Contest',
                                                 runner,
                                                 start_date,
                                                 end_date)
        contest.save()
        contest_player = contest.add_player(player)
        contest_player.save()
        beer = Beer.objects.create_beer('Reloaded Beer', 'Reloaded Brewery')
        contest_beer = contest.add_beer(beer)
        with self.assertRaises(CommandError):
            call_command('reload_checkin',
                         str(contest.id + 100),
                         'https://example.com/checkin/1',
                         '6-1-2017',
                         contest_player.user_name,
                         'Reloaded Beer',
                         'Reloaded Brewery',)

    def test_bad_player_reload_checkin(self):
        """Test whether the reload_checkin command fails on bad player input"""
        runner = Player.objects.get(id=4)
        player = Player.objects.get(id=1)
        player.save()
        start_date = timezone.make_aware(datetime.datetime(2017, 1, 1))
        end_date = timezone.make_aware(datetime.datetime(2017, 12, 31))
        contest = Contest.objects.create_contest('Contest',
                                                 runner,
                                                 start_date,
                                                 end_date)
        contest.save()
        contest_player = contest.add_player(player)
        contest_player.save()
        beer = Beer.objects.create_beer('Reloaded Beer', 'Reloaded Brewery')
        contest_beer = contest.add_beer(beer)
        with self.assertRaises(CommandError):
            call_command('reload_checkin',
                         str(contest.id),
                         'https://example.com/checkin/1',
                         '6-1-2017',
                         'not a player',
                         'Reloaded Beer',
                         'Reloaded Brewery',)

    def test_bad_beer_reload_checkin(self):
        """Test whether the reload_checkin command fails on bad input"""
        runner = Player.objects.get(id=4)
        player = Player.objects.get(id=1)
        player.save()
        start_date = timezone.make_aware(datetime.datetime(2017, 1, 1))
        end_date = timezone.make_aware(datetime.datetime(2017, 12, 31))
        contest = Contest.objects.create_contest('Contest',
                                                 runner,
                                                 start_date,
                                                 end_date)
        contest.save()
        contest_player = contest.add_player(player)
        contest_player.save()
        beer = Beer.objects.create_beer('Reloaded Beer', 'Reloaded Brewery')
        contest_beer = contest.add_beer(beer)
        with self.assertRaises(CommandError):
            call_command('reload_checkin',
                         str(contest.id),
                         'https://example.com/checkin/1',
                         '6-1-2017',
                         contest_player.user_name,
                         'not a beer',
                         'Reloaded Brewery',)

    def test_bad_brewery_reload_checkin(self):
        """Test whether the reload_checkin command fails on bad input"""
        runner = Player.objects.get(id=4)
        player = Player.objects.get(id=1)
        player.save()
        start_date = timezone.make_aware(datetime.datetime(2017, 1, 1))
        end_date = timezone.make_aware(datetime.datetime(2017, 12, 31))
        contest = Contest.objects.create_contest('Contest',
                                                 runner,
                                                 start_date,
                                                 end_date)
        contest.save()
        contest_player = contest.add_player(player)
        contest_player.save()
        beer = Beer.objects.create_beer('Reloaded Beer', 'Reloaded Brewery')
        contest_beer = contest.add_beer(beer)
        with self.assertRaises(CommandError):
            call_command('reload_checkin',
                         str(contest.id),
                         'https://example.com/checkin/1',
                         '6-1-2017',
                         contest_player.user_name,
                         'Reloaded Beer',
                         'not a brewery',)

    def test_bad_brewery_reload_checkin(self):
        """Test whether the reload_checkin command fails on bad input"""
        runner = Player.objects.get(id=4)
        player = Player.objects.get(id=1)
        player.save()
        start_date = timezone.make_aware(datetime.datetime(2017, 1, 1))
        end_date = timezone.make_aware(datetime.datetime(2017, 12, 31))
        contest = Contest.objects.create_contest('Contest',
                                                 runner,
                                                 start_date,
                                                 end_date)
        contest.save()
        contest_player = contest.add_player(player)
        contest_player.save()
        beer = Beer.objects.create_beer('Reloaded Beer', 'Reloaded Brewery')
        contest_beer = contest.add_beer(beer)
        with self.assertRaises(CommandError):
            call_command('reload_checkin',
                         str(contest.id),
                         'https://example.com/checkin/1',
                         '6-1-2017',
                         contest_player.user_name,
                         'Reloaded Beer',
                         'not a brewery',)

    def test_ambiguous_reload_checkin(self):
        """Test whether the reload_checkin command fails on ambiguous input"""
        runner = Player.objects.get(id=4)
        player = Player.objects.get(id=1)
        player.save()
        start_date = timezone.make_aware(datetime.datetime(2017, 1, 1))
        end_date = timezone.make_aware(datetime.datetime(2017, 12, 31))
        contest = Contest.objects.create_contest('Contest',
                                                 runner,
                                                 start_date,
                                                 end_date)
        contest.save()
        contest_player = contest.add_player(player)
        contest_player.save()
        beer = Beer.objects.create_beer('Reloaded Beer 1', 'Reloaded Brewery')
        contest_beer = contest.add_beer(beer)
        beer = Beer.objects.create_beer('Reloaded Beer 2', 'Reloaded Brewery')
        contest_beer = contest.add_beer(beer)
        with self.assertRaises(CommandError):
            call_command('reload_checkin',
                         str(contest.id),
                         'https://example.com/checkin/1',
                         '6-1-2017',
                         contest_player.user_name,
                         'Reloaded Beer',
                         'Reloaded Brewery',)

    def __write_checkin(self, entry):
        ename = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             'test-data', 'checkin', str(uuid.uuid4()))
        """
        if not hasattr(self, "base_checkin"):
            fname = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 'test-data', 'base-checkin.html')
            with open(fname, 'r') as file:
                self.base_checkin = Template(file.read())
        
        with open(ename, 'w') as file:
            if 'comment' in entry:
                comment_tag = "<p class=\"comment\">{}</p>".format(entry["comment"])
                file.write(self.base_checkin.substitute(entry, 
                                                        comment_tag=comment_tag))
            else:
                file.write(self.base_checkin.substitute(entry))
        """
        return ename
            

    def __build_rss_feed(self, rssfile, contest_player, feed):
        with open(rssfile, "w") as f:
            f.write("""<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0"
    xmlns:dc="http://purl.org/dc/elements/1.1/"
    xmlns:sy="http://purl.org/rss/1.0/modules/syndication/"
    xmlns:admin="http://webns.net/mvcb/"
    xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    xmlns:content="http://purl.org/rss/1.0/modules/content/"
	xmlns:atom="http://www.w3.org/2005/Atom">

    <channel>
    
    <title>Untappd</title>
    <link>file://localhost{}</link>
	<atom:link href="file://localhost{}" rel="self" type="application/rss+xml" />
	
    <description>Recent Brews on Untappd for {}</description>
    <dc:language>en</dc:language>
    <dc:creator>info@untappd.com</dc:creator>

    <dc:rights>Copyright 2017</dc:rights>
    <admin:generatorAgent rdf:resource="http://www.codeigniter.com/" />""".format(
            rssfile, rssfile, contest_player.user_name))
            for entry in feed:
                entry_url = "file://localhost" + self.__write_checkin(entry)
                f.write("""     <item>

          <title>{} is drinking a {} by {} at Iron Horse Tap Room</title>
          <link>{}</link>
			
          <guid>{}</guid>

		<description>{}</description>
      	<pubDate>{}</pubDate>
        </item>
""".format(contest_player.user_name, entry["beer_name"], entry["brewery_name"],
           entry_url, entry_url, entry.get("comment", None), entry["time"]))
                entry["untappd_checkin"] = entry_url
            f.write("</channel></rss>\n")
                

    def __load_contest_from_test(self, creator, contest_dict):
        player = Player.objects.get(user__username=creator)
        contest = Contest.objects.create_contest(contest_dict["name"], 
                                                 player, 
                                                 contest_dict["start_date"],
                                                 contest_dict["end_date"])
        for beer_dict in contest_dict["beers"]:
            beer = Beer.objects.create_beer(beer_dict["beer_name"],
                                            beer_dict["brewery_name"],
                                            untappd_url=beer_dict["beer_url"],
                                            brewery_url=beer_dict["brewery_url"])
            contest.add_beer(beer, point_value=beer_dict["points"])
        for bonus_dict in contest_dict["bonuses"]:
            contest.add_bonus(bonus_dict["name"], bonus_dict["description"],
                              bonus_dict["hashtags"])
        return contest
            
    def __run_rss_contest_test(self, test):
        contest = self.__load_contest_from_test("user1", test["contest"])
        user = User.objects.get(username="user2")
        slug = re.sub(r'\s+', '-', test["contest"]["name"].lower())
# rssfile = os.path.join(os.path.dirname(os.path.abspath(__file__)),
#'test-data', 'test-' + slug + '.xml')
        player = Player.objects.get(user=user)
        with tempfile.NamedTemporaryFile(delete=False) as rsstmpfile:
            rssfile = rsstmpfile.name
            player.untappd_rss = 'file://localhost' + rssfile
            player.save()
            contest_player = contest.add_player(player)
            self.__build_rss_feed(rssfile, contest_player, test["feed"])
            load_player_checkins(player, contest.id)
            for fbeer in test["feed"]:
                uv = Unvalidated_Checkin.objects.get(
                            untappd_checkin=fbeer["untappd_checkin"])
                self.assertEqual(fbeer["has_possibles"], uv.has_possibles,
                                 "{} mismatched has_possibles".format(uv))
                if "possible_bonuses" in fbeer:
                    self.assertIsNotNone(uv.possible_bonuses)
                    ids = [Contest_Bonus.objects.get(name=name).id 
                           for name in fbeer["possible_bonuses"]]
                             
                    self.assertEqual(sorted(uv.possible_bonuses), 
                                     sorted(ids),
                                     "Should have possible bonuses {}".format(uv))
                else:
                    self.assertIsNone(uv.possible_bonuses)

    def test_rss_loader(self):
        """Tests the RSS feed loader"""
        def timestring(year, month, day, hour, minute):
            return datetime.datetime(year, month, day, hour, minute).strftime(
                    '%a, %d %b %Y %H:%M:00 +0000')
        tests = [
            {
                "contest": {
                    "name": "RSS Contest 1",
                    "start_date": timezone.make_aware(datetime.datetime(2017, 1, 1)),
                    "end_date": timezone.make_aware(datetime.datetime(2017, 12, 31)),
                    "beers": [ 
                        {
                            "beer_name": "Beer 1",
                            "brewery_name": "Brewery 1",
                            "beer_url": "https://untappd.com/b/beer1",
                            "brewery_url": "https://untappd.com/brewery/brewery1",
                            "points": 1,
                        },
                        {
                            "beer_name": "Beer 2",
                            "brewery_name": "Brewery 2",
                            "beer_url": "https://untappd.com/b/beer2",
                            "brewery_url": "https://untappd.com/brewery/brewery2",
                            "points": 1,
                        },
                        {
                            "beer_name": "Beer 3",
                            "brewery_name": "Brewery 3",
                            "beer_url": "https://untappd.com/b/beer3",
                            "brewery_url": "https://untappd.com/brewery/brewery3",
                            "points": 1,
                        },
                    ],
                    "bonuses": [
                    ]
                },
                "feed": [ 
                    { 
                        "beer_name": "Beer 1", 
                        "beer_url": "https://untappd.com/b/beer1",
                        "brewery_name": "Brewery 1",
                        "brewery_url": "https://untappd.com/brewery/brewery1",
                        "time": timestring(2017, 2, 9, 12, 0), 
                        "has_possibles": True,
                    },
                    { 
                        "beer_name": "Beer 6", 
                        "beer_url": "https://untappd.com/b/beer6",
                        "brewery_name": "Brewery 6",
                        "brewery_url": "https://untappd.com/brewery/brewery7",
                        "time": timestring(2017, 3, 9, 12, 0), 
                        "has_possibles": False,
                    },
                    { 
                        "beer_name": "Beer 7", 
                        "beer_url": "https://untappd.com/b/beer7",
                        "brewery_name": "Brewery 7",
                        "brewery_url": "https://untappd.com/brewery/brewery7",
                        "time": timestring(2017, 3, 19, 12, 0), 
                        "has_possibles": False,
                    },
                    { 
                        "beer_name": "Beer 8", 
                        "beer_url": "https://untappd.com/b/beer8",
                        "brewery_name": "Brewery 8",
                        "brewery_url": "https://untappd.com/brewery/brewery8",
                        "time": timestring(2017, 4, 9, 12, 0), 
                        "has_possibles": False,
                    },
                    { 
                        "beer_name": "Beer 3", 
                        "beer_url": "https://untappd.com/b/beer3",
                        "brewery_name": "Brewery 3",
                        "brewery_url": "https://untappd.com/brewery/brewery3",
                        "time": timestring(2017, 4, 12, 12, 0), 
                        "has_possibles": True,
                    },
                ]
            },
            {
                "contest": {
                    "name": "RSS Contest 2",
                    "start_date": timezone.make_aware(datetime.datetime(2017, 1, 1)),
                    "end_date": timezone.make_aware(datetime.datetime(2017, 12, 31)),
                    "beers": [ 
                        {
                            "beer_name": "Beer 1",
                            "brewery_name": "Brewery 1",
                            "beer_url": "https://untappd.com/b/beer1",
                            "brewery_url": "https://untappd.com/brewery/brewery1",
                            "points": 1,
                        },
                        {
                            "beer_name": "Beer 2",
                            "brewery_name": "Brewery 2",
                            "beer_url": "https://untappd.com/b/beer2",
                            "brewery_url": "https://untappd.com/brewery/brewery2",
                            "points": 1,
                        },
                        {
                            "beer_name": "Beer 3",
                            "brewery_name": "Brewery 3",
                            "beer_url": "https://untappd.com/b/beer3",
                            "brewery_url": "https://untappd.com/brewery/brewery3",
                            "points": 1,
                        },
                    ],
                    "bonuses": [
                        {
                            "name": "bonus1",
                            "description": "Bonus 1",
                            "hashtags": "bonus1",
                        },
                        {
                            "name": "bonus2",
                            "description": "Bonus 2",
                            "hashtags": "bonus2,anotherbonus",
                        },
                    ]
                },
                "feed": [ 
                    { 
                        "beer_name": "Beer 1", 
                        "beer_url": "https://untappd.com/b/beer1",
                        "brewery_name": "Brewery 1",
                        "brewery_url": "https://untappd.com/brewery/brewery1",
                        "time": timestring(2017, 2, 9, 12, 0), 
                        "has_possibles": True,
                    },
                    { 
                        "beer_name": "Beer 7", 
                        "beer_url": "https://untappd.com/b/beer7",
                        "brewery_name": "Brewery 7",
                        "brewery_url": "https://untappd.com/brewery/brewery7",
                        "comment": "This is a #bonus1",
                        "time": timestring(2017, 3, 9, 12, 0), 
                        "has_possibles": False,
                        "possible_bonuses": [ "bonus1", ],
                    },
                    { 
                        "beer_name": "Beer 7", 
                        "beer_url": "https://untappd.com/b/beer7",
                        "brewery_name": "Brewery 7",
                        "brewery_url": "https://untappd.com/brewery/brewery7",
                        "time": timestring(2017, 3, 19, 12, 0), 
                        "has_possibles": False,
                    },
                    { 
                        "beer_name": "Beer 8", 
                        "beer_url": "https://untappd.com/b/beer8",
                        "brewery_name": "Brewery 8",
                        "brewery_url": "https://untappd.com/brewery/brewery8",
                        "time": timestring(2017, 4, 9, 12, 0), 
                        "has_possibles": False,
                    },
                    { 
                        "beer_name": "Beer 3", 
                        "beer_url": "https://untappd.com/b/beer3",
                        "brewery_name": "Brewery 3",
                        "brewery_url": "https://untappd.com/brewery/brewery3",
                        "comment": "#anotherbonus for you",
                        "time": timestring(2017, 4, 12, 12, 0), 
                        "has_possibles": True,
                        "possible_bonuses": [ "bonus2", ],
                    },
                ]
            }
        ]
        for test in tests:
            self.__run_rss_contest_test(test)
            

    def test_rss_load_beer_matches(self):
        """Tests the loading of files from RSS with some potential matches"""
        pass

    def test_rss_load_no_matches(self):
        """Tests the loading of files from RSS with no potential matches"""
        pass

    def test_rss_load_bonus_matches(self):
        """Tests the loading of files from RSS with no potential matches"""
        pass


