from django.test import TestCase, override_settings
from django.test import Client
from django.contrib.auth.models import User, Group, Permission
from beers.models import Contest, Player, Contest_Player

@override_settings(ROOTURL_CONF='beers.urls', SSLIFY_DISABLE=True)
class BeersViewsTestCase(TestCase):
    """Tests the views for the beer models"""

    def setUp(self):
        # Create a player and a contest runner (who is also aplayer)
        # Gotta make a fixture for this....
        self.playerGroup = Group.objects.create(name='G_Player')
        self.playerGroup.permissions.add(Permission.objects.get(codename='add_checkin'))
        self.playerGroup.permissions.add(Permission.objects.get(codename='delete_checkin'))
        self.playerGroup.permissions.add(Permission.objects.get(codename='change_checkin'))
        self.playerGroup.save()
        self.runnerGroup = Group.objects.create(name='G_ContestRunner')
        self.runnerGroup.permissions.add(Permission.objects.get(codename='add_checkin'))
        self.runnerGroup.permissions.add(Permission.objects.get(codename='delete_checkin'))
        self.runnerGroup.permissions.add(Permission.objects.get(codename='change_checkin'))
        self.runnerGroup.permissions.add(Permission.objects.get(codename='add_player'))
        self.runnerGroup.permissions.add(Permission.objects.get(codename='delete_player'))
        self.runnerGroup.permissions.add(Permission.objects.get(codename='change_player'))
        self.runnerGroup.permissions.add(Permission.objects.get(codename='add_contest'))
        self.runnerGroup.permissions.add(Permission.objects.get(codename='delete_contest'))
        self.runnerGroup.permissions.add(Permission.objects.get(codename='change_contest'))
        self.runnerGroup.save()
        self.playerUser = User.objects.create_user('player1',
                    email='fake@example.com',
                    first_name='First',
                    last_name='Last',
                    password='player1_password')
        self.playerUser.groups.add(self.playerGroup)
        self.playerUser.save()
        self.player = Player.create(self.playerUser, '', 'http://localhost/', 'none')
        self.player.save()
        self.runnerUser = User.objects.create_user('runner1',
                    email='fake@example.com',
                    first_name='Runner',
                    last_name='Last',
                    password='runner1_password')
        self.runnerUser.groups.add(self.playerGroup)
        self.runnerUser.groups.add(self.runnerGroup)
        self.runnerUser.save()
        self.runner = Player.create(self.runnerUser, '', 'http://localhost/', 'none')
        self.runner.save()

    def test_profile(self):
        c = Client()
        self.assertTrue(c.login(username='runner1', password='runner1_password'))

        response = c.get('/profile')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/profile.html')
        # self.assertInHTML('none', str(response.content))

    def test_create_contest_success(self):
        c = Client()
        self.assertTrue(c.login(username='runner1', password='runner1_password'))

        response = c.post('/contests/add', follow=True,
                            data={ 'name': 'Contest-Success-1',
                                  'start_date': '2016-01-01',
                                  'end_date': '2017-01-01' })
        self.assertEqual(Contest.objects.filter(name='Contest-Success-1').count(), 1)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'beers/contest-add-success.html')
        # self.assertInHTML('added!', str(response.content))
