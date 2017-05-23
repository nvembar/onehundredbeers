from django.test import TestCase, override_settings
from django.test import Client
from django.contrib.auth.models import User, Group, Permission
from beers.models import Contest, Player, Contest_Player
import datetime

@override_settings(ROOTURL_CONF='beers.urls', SECURE_SSL_REDIRECT=False)
class BeersViewsTestCase(TestCase):
    """Tests the views for the beer models"""

    fixtures = ['permissions', 'users']

    def setUp(self):
        # Create a player and a contest runner (who is also aplayer)
        # Gotta make a fixture for this....
        runner = Player.objects.get(user__username='runner1')
        self.contest = Contest.objects.create_contest('Contest', runner,
                    datetime.datetime(2016, 1, 1,
                        tzinfo=datetime.timezone(datetime.timedelta(hours=-5))),
                    datetime.datetime(2017, 1, 1,
                        tzinfo=datetime.timezone(datetime.timedelta(hours=-5))))
        self.contest.save()

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
        self.assertTrue(c.login(username='user1', password='password1%'))
        response = c.post('/contests/{}/join'.format(self.contest.id),
                            data={'action': 'join'})
