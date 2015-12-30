import django

django.setup()

from django.contrib.auth.models import Group, Permission
from beers.models import Contest, Contest_Beer, Contest_Player, Checkin, Player

cr_group, created = Group.objects.get_or_create(name='G_ContestRunner')
cr_permissions = ['add_contest', 'delete_contest', 'change_contest',
                  'add_contest_player', 'delete_contest_player',
                  'change_contest_player',
                  'add_contest_beer', 'delete_contest_beer',
                  'change_contest_beer',
                  'add_checkin', 'delete_checkin', 'change_checkin',
                  'add_player', 'delete_player', 'change_player']
if created:
    for codename in cr_permissions:
        print("Adding permission {0} to {1}".format(codename, cr_group.name))
        p = Permission.objects.get(codename=codename)
        cr_group.permissions.add(p)

player_group, created = Group.objects.get_or_create(name='G_Player')
player_permissions = ['add_checkin', 'delete_checkin', 'change_checkin']
if created:
    for codename in player_permissions:
        print("Adding permission {0} to {1}".format(codename, cr_group.name))
        p = Permission.objects.get(codename=codename)
        player_group.permissions.add(p)
