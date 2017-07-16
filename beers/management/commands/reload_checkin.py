"""Command to load a specific checkin for a user"""

import datetime
from dateutil.parser import parse
from django.core.management.base import BaseCommand, CommandError
from beers.models import Beer, Player, Contest_Beer, Contest, Contest_Player

class Command(BaseCommand):
    """Command which loads a specific checkin with the given information"""

    help = 'Loads a specific checkin with the given information'

    def add_arguments(self, parser):
        parser.add_argument('contest_id', nargs=1, help='Contest ID', type=int)
        parser.add_argument('untappd_url',
                            nargs=1,
                            help='Untapped URL of the checkin')
        parser.add_argument('checkin_time', nargs=1, help='Checkin time')
        parser.add_argument('player', nargs=1, help='Player name')
        parser.add_argument('beer', nargs=1, help='Beer name')
        parser.add_argument('brewery', nargs=1, help='Brewery name')

    def handle(self, *args, **opts):
        beer = None
        player = None
        contest_player = None
        contest_beer = None
        contest = None
        untappd_url = opts['untappd_url'][0]
        contest_id = opts['contest_id'][0]
        checkin_time = None
        try:
            default_date = datetime.datetime(year=1970, month=1, day=1)
            checkin_time = parse(opts['checkin_time'][0],
                                 default=default_date)
            if checkin_time.year == 1970:
                raise CommandError(('Date in invalid format: '
                                    + ' {0}').format(opts['checkin_time']))
        except ValueError as e:
            raise CommandError(('Date in invalid format: '
                                + '{0}: {1}').format(e, opts['checkin_time']))
        try:
            beers = Beer.objects.filter(name__icontains=opts['beer'][0],
                                        brewery__icontains=opts['brewery'][0])
            contest_beer = Contest_Beer.objects.get(contest_id=contest_id,
                                                    beer=beers[0])
        except IndexError:
            raise CommandError(('Unable to find beer '
                                + ' "{0}" by "{1}"').format(opts['beer'],
                                                            opts['brewery']))
        except Contest_Beer.DoesNotExist:
            raise CommandError(('Unable to find beer/contest pairing: '
                                + ' {0}/{1}').format(contest_id, beer.id))
        try:
            contest = Contest.objects.get(id=contest_id)
        except Contest.DoesNotExist:
            raise CommandError('Unable to find contest {0}'.format(contest_id))
        try:
            player = Player.objects.get(user__username=opts['player'][0])
        except Player.DoesNotExist:
            raise CommandError(('Unable to find user '
                                + '"{0}"').format(opts['player'][0]))
        try:
            contest_player = Contest_Player.objects.get(contest=contest,
                                                        player_id=player.id)
        except Contest_Player.DoesNotExist:
            raise CommandError(('Player "{0}" is not affiliated with '
                                + 'contest "{1}"').format(opts['player'][0],
                                                          contest))
        contest_player.drink_beer(contest_beer,
                                  data={'untappd_checkin': untappd_url,
                                        'checkin_time': checkin_time})
