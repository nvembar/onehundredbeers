"""Command that will load checkins for a user"""

import argparse
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from beers.models import Player, Contest
from beers.utils.checkin import load_player_checkins
from dateutil.parser import parse as date_parse


def convert_to_date(arg):
    "Converts a string to a timezone aware date"
    try:
        after_date = date_parse(arg)
    except ValueError:
        raise argparse.ArgumentTypeError(('Error: load-checkins got a '
                                          + 'malformed date: {}').format(arg))
    return timezone.make_aware(after_date)


class Command(BaseCommand):
    """
    A command which loads checkins for a player or many players for a
    given contest.
    """

    help = 'Loads checkins across contests'

    def add_arguments(self, parser):
        """There are three optional arguments for the command:
           --player: the user name of the player
           --contest: the Contest ID
           --after-date: The date after which to filter the results
        """
        parser.add_argument('--player', nargs=1, help='Player')
        parser.add_argument('--contest', nargs=1, help='Contest ID', type=int)
        parser.add_argument('--after-date', nargs=1, help='After date',
                            type=convert_to_date)

    def handle(self, *args, **opts):
        """
        Primarily calls load_player_checkins with the right arguments
        """
        players = Player.objects.all()
        contest_id = None
        after_date = None
        if 'player' in opts and opts['player']:
            players = players.filter(user__username=opts['player'][0])
            if players.count() == 0:
                raise CommandError(('Error: no such player: '
                                    + '{}').format(opts['player'][0]))
        if 'contest' in opts and opts['contest']:
            try:
                contest_id = opts['contest'][0]
                Contest.objects.get(id=contest_id)
            except Contest.DoesNotExist:
                raise CommandError(('Error: load-checkins got a contest that'
                                    + ' did not exist: {}').format(contest_id))
        if 'after_date' in opts and opts['after_date']:
            after_date = opts['after_date'][0]
        for player in players:
            load_player_checkins(player, from_date=after_date,
                                 contest_id=contest_id)
