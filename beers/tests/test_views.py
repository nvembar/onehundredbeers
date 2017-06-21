from django.test import TransactionTestCase, TestCase, override_settings
from django.test import Client
from django.contrib.auth.models import User, Group, Permission
from django.core.urlresolvers import reverse
from django.utils import timezone
from beers.models import Contest, Player, Contest_Player, Contest_Checkin, Contest_Beer
import datetime

@override_settings(ROOTURL_CONF='beers.urls', SECURE_SSL_REDIRECT=False)
class BeersViewsTestCase(TestCase):
    """Tests the views for the beer models"""

    fixtures = ['permissions', 'users', 'contest_tests']

    def setUp(self):
        # Create a player and a contest runner (who is also aplayer)
        # Gotta make a fixture for this....
        runner = Player.objects.get(user__username='runner1')

    def test_profile_view(self):
        "Tests that a profile can be viewed by the user"
        c = Client()
        self.assertTrue(c.login(username='runner1', password='password1%'))

        response = c.get('/profile')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/profile.html')
        # self.assertInHTML('none', str(response.content))
    def test_create_contest_success(self):
        "Tests that a contest runner can create a new contest"
        c = Client()
        runner = Player.objects.get(user__username='runner1')
        self.assertTrue(c.login(username='runner1', password='password1%'))

        response = c.post('/contests/add',
                            data={ 'name': 'Contest-Success-1',
                                  'start_date': '2016-01-01',
                                  'end_date': '2017-01-01' })
        self.assertEqual(Contest.objects.filter(name='Contest-Success-1').count(), 1)
        contest = Contest.objects.get(name='Contest-Success-1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(contest.creator.id, runner.id)
        self.assertTemplateUsed(response, 'beers/contest-add-success.html')
        # self.assertInHTML('added!', str(response.content))

    def test_create_contest_permission(self):
        """Tests that a contest player that isn't a runner cannot start a new
        contest"""
        c = Client()
        self.assertTrue(c.login(username='user1', password='password1%'))

        response = c.post('/contests/add',
                            data={ 'name': 'Contest-Failure-1',
                                  'start_date': '2016-01-01',
                                  'end_date': '2017-01-01' })
        self.assertNotEqual(response.status_code, 200)
        self.assertEqual(Contest.objects.filter(name='Contest-Failure-1').count(), 0)

    def test_create_contest_baddate(self):
        """
        Tests that a contest cannot have an end date before a start date
        """
        c = Client()
        self.assertTrue(c.login(username='runner1', password='password1%'))

        response = c.post('/contests/add',
                            data={ 'name': 'Contest-Failure-1',
                                  'start_date': '2016-01-01',
                                  'end_date': '2015-01-01' })
        self.assertEqual(Contest.objects.filter(name='Contest-Failure-1').count(), 0)
        self.assertTemplateNotUsed(response, 'beers/contest-add-success.html')

    def test_join_contest(self):
        """
        Tests that a contest player can join a contest
        """
        c = Client()
        player = Player.objects.get(id=4)
        self.assertTrue(player.user.username, 'runner1')
        contest = Contest.objects.get(name='Contest 1')
        self.assertTrue(c.login(username='user5', password='password1%'))
        response = c.post(reverse('contest-join', args=[contest.id]), data={'action': 'join'})
        self.assertTrue(Contest_Player.objects.filter(contest_id=contest.id, user_name='user5').count(), 1)

    def test_basic_leaderboard(self):
        """
        Tests that a simple sequential ranking works as expected
        """
        # Add validated checkins to the contest
        user1 = Contest_Player.objects.get(user_name='user1')
        user2 = Contest_Player.objects.get(user_name='user2')
        user3 = Contest_Player.objects.get(user_name='user3')
        user4 = Contest_Player.objects.get(user_name='user4')
        contest = Contest.objects.get(name='Contest 1')
        user1.beer_count = 2
        user1.total_points = 6
        user1.beer_points = 3
        user1.brewery_points = 3
        user1.save()
        user2.beer_count = 2
        user2.total_points = 4
        user2.beer_points = 4
        user2.brewery_points = 0
        user2.save()
        user3.beer_count = 1
        user3.total_points = 3
        user3.beer_points = 3
        user3.brewery_points = 0
        user3.save()
        user4.beer_count = 1
        user4.total_points = 1
        user4.beer_points = 0
        user4.brewery_points = 1
        user4.save()
        checkin_date = timezone.make_aware(datetime.datetime(2016, 6, 1))
        Contest_Checkin.objects.create_checkin(user1,
                        Contest_Beer.objects.get(contest=contest, beer_name='Beer 4'),
                        checkin_date, 'https://example.com/checkin/user1/beer4')
        Contest_Checkin.objects.create_checkin(user1,
                        Contest_Beer.objects.get(contest=contest, beer_name='Beer 5'),
                        checkin_date, 'https://example.com/checkin/user1/beer5')
        Contest_Checkin.objects.create_checkin(user2,
                        Contest_Beer.objects.get(contest=contest, beer_name='Beer 4'),
                        checkin_date, 'https://example.com/checkin/user2/beer4')
        Contest_Checkin.objects.create_checkin(user2,
                        Contest_Beer.objects.get(contest=contest, beer_name='Beer 1'),
                        checkin_date, 'https://example.com/checkin/user2/beer1')
        Contest_Checkin.objects.create_checkin(user3,
                        Contest_Beer.objects.get(contest=contest, beer_name='Beer 4'),
                        checkin_date, 'https://example.com/checkin/user3/beer4')
        Contest_Checkin.objects.create_checkin(user4,
                        Contest_Beer.objects.get(contest=contest, beer_name='Beer 1'),
                        checkin_date, 'https://example.com/checkin/user4/beer1')
        c = Client()
        response = c.get(reverse('leaderboard', args=[contest.id]))
        players = response.context['players']
        self.assertEqual(players[0].id, user1.id)
        self.assertEqual(players[0].rank, 1)
        self.assertEqual(players[1].id, user2.id)
        self.assertEqual(players[1].rank, 2)
        self.assertEqual(players[2].id, user3.id)
        self.assertEqual(players[2].rank, 3)
        self.assertEqual(players[3].id, user4.id)
        self.assertEqual(players[3].rank, 4)

    def test_tied_leaderboard(self):
        """
        Tests that the 1224 ranking works as expected
        """
        # Add validated checkins to the contest
        user1 = Contest_Player.objects.get(user_name='user1')
        user2 = Contest_Player.objects.get(user_name='user2')
        user3 = Contest_Player.objects.get(user_name='user3')
        user4 = Contest_Player.objects.get(user_name='user4')
        contest = Contest.objects.get(name='Contest 1')
        user1.beer_count = 2
        user1.total_points = 6
        user1.beer_points = 3
        user1.brewery_points = 3
        user1.save()
        user2.beer_count = 2
        user2.total_points = 4
        user2.beer_points = 4
        user2.brewery_points = 0
        user2.save()
        user3.beer_count = 2
        user3.total_points = 4
        user3.beer_points = 4
        user3.brewery_points = 0
        user3.save()
        user4.beer_count = 1
        user4.total_points = 1
        user4.beer_points = 0
        user4.brewery_points = 1
        user4.save()
        checkin_date = timezone.make_aware(datetime.datetime(2016, 6, 1))
        Contest_Checkin.objects.create_checkin(user1,
                        Contest_Beer.objects.get(contest=contest, beer_name='Beer 4'),
                        checkin_date, 'https://example.com/checkin/user1/beer4')
        Contest_Checkin.objects.create_checkin(user1,
                        Contest_Beer.objects.get(contest=contest, beer_name='Beer 5'),
                        checkin_date, 'https://example.com/checkin/user1/beer5')
        Contest_Checkin.objects.create_checkin(user2,
                        Contest_Beer.objects.get(contest=contest, beer_name='Beer 4'),
                        checkin_date, 'https://example.com/checkin/user2/beer4')
        Contest_Checkin.objects.create_checkin(user2,
                        Contest_Beer.objects.get(contest=contest, beer_name='Beer 1'),
                        checkin_date, 'https://example.com/checkin/user2/beer1')
        Contest_Checkin.objects.create_checkin(user3,
                        Contest_Beer.objects.get(contest=contest, beer_name='Beer 5'),
                        checkin_date, 'https://example.com/checkin/user3/beer5')
        Contest_Checkin.objects.create_checkin(user3,
                        Contest_Beer.objects.get(contest=contest, beer_name='Beer 3'),
                        checkin_date, 'https://example.com/checkin/user3/beer3')
        Contest_Checkin.objects.create_checkin(user4,
                        Contest_Beer.objects.get(contest=contest, beer_name='Beer 1'),
                        checkin_date, 'https://example.com/checkin/user4/beer1')
        c = Client()
        response = c.get(reverse('leaderboard', args=[contest.id]))
        players = response.context['players']
        self.assertEqual(players[0].id, user1.id)
        self.assertEqual(players[0].rank, 1)
        self.assertEqual(players[1].id, user2.id)
        self.assertEqual(players[1].rank, 2)
        self.assertEqual(players[2].id, user3.id)
        self.assertEqual(players[2].rank, 2)
        self.assertEqual(players[3].id, user4.id)
        self.assertEqual(players[3].rank, 4)

    def test_leaderboard_tied_at_end(self):
        """
        Tests that the 1224 ranking works as expected
        """
        # Add validated checkins to the contest
        user1 = Contest_Player.objects.get(user_name='user1')
        user2 = Contest_Player.objects.get(user_name='user2')
        user3 = Contest_Player.objects.get(user_name='user3')
        user4 = Contest_Player.objects.get(user_name='user4')
        contest = Contest.objects.get(name='Contest 1')
        user1.beer_count = 2
        user1.total_points = 6
        user1.beer_points = 3
        user1.brewery_points = 3
        user1.save()
        user2.beer_count = 2
        user2.total_points = 4
        user2.beer_points = 4
        user2.brewery_points = 0
        user2.save()
        user3.beer_count = 1
        user3.total_points = 1
        user3.beer_points = 0
        user3.brewery_points = 1
        user3.save()
        user4.beer_count = 1
        user4.total_points = 1
        user4.beer_points = 0
        user4.brewery_points = 1
        user4.save()
        checkin_date = timezone.make_aware(datetime.datetime(2016, 6, 1))
        Contest_Checkin.objects.create_checkin(user1,
                        Contest_Beer.objects.get(contest=contest, beer_name='Beer 4'),
                        checkin_date, 'https://example.com/checkin/user1/beer4')
        Contest_Checkin.objects.create_checkin(user1,
                        Contest_Beer.objects.get(contest=contest, beer_name='Beer 5'),
                        checkin_date, 'https://example.com/checkin/user1/beer5')
        Contest_Checkin.objects.create_checkin(user2,
                        Contest_Beer.objects.get(contest=contest, beer_name='Beer 4'),
                        checkin_date, 'https://example.com/checkin/user2/beer4')
        Contest_Checkin.objects.create_checkin(user2,
                        Contest_Beer.objects.get(contest=contest, beer_name='Beer 1'),
                        checkin_date, 'https://example.com/checkin/user2/beer1')
        Contest_Checkin.objects.create_checkin(user3,
                        Contest_Beer.objects.get(contest=contest, beer_name='Beer 3'),
                        checkin_date, 'https://example.com/checkin/user3/beer3')
        Contest_Checkin.objects.create_checkin(user4,
                        Contest_Beer.objects.get(contest=contest, beer_name='Beer 1'),
                        checkin_date, 'https://example.com/checkin/user4/beer1')
        c = Client()
        response = c.get(reverse('leaderboard', args=[contest.id]))
        players = response.context['players']
        self.assertEqual(players[0].id, user1.id)
        self.assertEqual(players[0].rank, 1)
        self.assertEqual(players[1].id, user2.id)
        self.assertEqual(players[1].rank, 2)
        self.assertEqual(players[2].id, user3.id)
        self.assertEqual(players[2].rank, 3)
        self.assertEqual(players[3].id, user4.id)
        self.assertEqual(players[3].rank, 3)
