"""
Tests the loader utilities and commands for the hundred beers app
"""

import datetime
import io
import os
from unittest.mock import patch, MagicMock
import boto3
import botocore.session
from botocore.stub import Stubber
from django.test import TestCase, override_settings
from django.utils import timezone
from django.core.management import call_command
from django.core.management.base import CommandError
from beers.models import Contest_Beer, Beer, Contest, Player, \
                         Unvalidated_Checkin
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

    def test_successful_feed_for_player(self):
        """Test the ability to load a single XML feed file for a user"""
        runner = Player.objects.get(id=4)
        player = Player.objects.get(id=1)
        player.untappd_rss = os.path.join(BASE_DIR,
                                          '..',
                                          'test-data',
                                          'test-checkins.xml')
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

    def test_successful_feed_for_player_twice(self):
        """
        Test the ability to load a single XML feed file for a user twice.
        The second call shouldn't add any new checkins because they'd be
        redundant
        """
        runner = Player.objects.get(id=4)
        player = Player.objects.get(id=1)
        player.untappd_rss = os.path.join(BASE_DIR,
                                          '..',
                                          'test-data',
                                          'test-checkins.xml')
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

    def test_successful_feed_after_date(self):
        """Tests the ability to load a subset of a XML feed after a certain date"""
        runner = Player.objects.get(id=4)
        player = Player.objects.get(id=1)
        player.untappd_rss = os.path.join(BASE_DIR, '..', 'test-data', 'test-checkins.xml')
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

    def test_successful_checkin_command_for_player(self):
        """Tests whether the checkin command works for a single player"""
        runner = Player.objects.get(id=4)
        player = Player.objects.get(id=1)
        player.untappd_rss = os.path.join(BASE_DIR, '..', 'test-data', 'test-checkins.xml')
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

    def test_successful_checkin_command_for_player_after_date(self):
        """Test the ability to load a single XML feed file for a user"""
        runner = Player.objects.get(id=4)
        player = Player.objects.get(id=1)
        player.untappd_rss = os.path.join(BASE_DIR,
                                          '..',
                                          'test-data',
                                          'test-checkins.xml')
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

    def test_successful_checkin_command_for_all(self):
        """Test the ability to load a single XML feed file for a user"""
        runner = Player.objects.get(id=4)
        runner.untappd_rss = os.path.join(BASE_DIR,
                                          '..',
                                          'test-data',
                                          'test-checkins.xml')
        runner.save()
        player = Player.objects.get(id=1)
        player.untappd_rss = os.path.join(BASE_DIR,
                                          '..',
                                          'test-data',
                                          'test-checkins.xml')
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
        contest_runner = contest.add_player(runner)
        contest_runner.save()
        call_command('load_checkins')
        self.assertEqual(Unvalidated_Checkin.objects.all().count(), 50)

    def test_successful_checkin_command_for_all_after_date(self):
        """Test the ability to load a single XML feed file for a user"""
        runner = Player.objects.get(id=4)
        runner.untappd_rss = os.path.join(BASE_DIR,
                                          '..',
                                          'test-data',
                                          'test-checkins.xml')
        runner.save()
        player = Player.objects.get(id=1)
        player.untappd_rss = os.path.join(BASE_DIR,
                                          '..',
                                          'test-data',
                                          'test-checkins.xml')
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
        contest_runner = contest.add_player(runner)
        contest_runner.save()
        call_command('load_checkins', '--after-date', '2017-06-01')
        self.assertEqual(Unvalidated_Checkin.objects.all().count(), 8)

    def test_unsucessful_checkin_command_with_bad_contest(self):
        """Test whether a checkin command with bad contest arguments fails"""
        with self.assertRaises(CommandError):
            call_command('load_checkins', '--contest', 'bad bad')
        with self.assertRaises(CommandError):
            call_command('load_checkins', '--contest', 1000)

    def test_unsucessful_checkin_command_with_bad_player(self):
        """Test whether a checkin command with bad player argument fails"""
        with self.assertRaises(CommandError):
            call_command('load_checkins', '--player', 'no such player')

    def test_unsucessful_checkin_command_with_bad_after_date(self):
        """Test whether a checkin command with bad date argument fails"""
        with self.assertRaises(CommandError):
            call_command('load_checkins', '--after-date', 'is not a date')
