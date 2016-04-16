import django
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Model
from beers.models import Beer, Player, Contest_Checkin, Contest_Beer, Contest, Contest_Player
import argparse
import sys
from dateutil.parser import parse
import datetime

class Command(BaseCommand):
    help = 'Loads a specific checkin with the given information'

    def add_arguments(self, parser):
        parser.add_argument('contest_id', nargs=1, help='Contest ID')
        parser.add_argument('untappd_url', nargs=1, help='Untapped URL of the checkin')
        parser.add_argument('checkin_time', nargs=1, help='Checkin time')
        parser.add_argument('player', nargs=1, help='Player name')
        parser.add_argument('beer', nargs=1, help='Beer name')
        parser.add_argument('brewery', nargs=1, help='Brewery name')

    def handle(self, *args, **opts):
        beer = None
        player = None
        cp = None
        cb = None
        untappd_url = opts['untappd_url'][0]
        checkin_time = parse(opts['checkin_time'][0],
                default=datetime.datetime(year=1970, month=1, day=1))
        if checkin_time.year == 1970:
            raise CommandError("Date in invalid format: {0}".format(opts['checkin_time']))
        try:
            beer = Beer.objects.filter(name__icontains=opts['beer'][0],
                                    brewery__icontains=opts['brewery'][0])[0]
            cb = Contest_Beer.objects.get(contest_id=opts['contest_id'][0], beer_id=beer.id)
        except IndexError:
            raise CommandError("Unable to find beer '{0}' by '{1}'".format(opts['beer'], opts['brewery']))
        except Contest_Beer.DoesNotExist:
            raise CommandError("Unable to find beer/contest pairing: {0}/{1}".format(contest, beer.id))
        try:
            contest = Contest.objects.get(id=opts['contest_id'][0])
        except Contest.DoesNotExist:
            raise CommandError("Unable to find contest '{0}'".format(opts['contest_id']))
        try:
            player = Player.objects.get(user__username=opts['player'][0])
        except Player.DoesNotExist:
            raise CommandError("Unable to find user '{0}'".format(opts['player']))
        try:
            cp = Contest_Player.objects.get(contest_id=opts['contest_id'][0], player_id=player.id)
        except Contest_Player.DoesNotExist:
            raise CommandError("Player '{0}' is not affiliated with contest '{1}'".format(opts['player'], opts['contest_id']))
        c = Contest_Checkin.objects.create(contest_player=cp, checkin_time=checkin_time,
                    untappd_checkin=untappd_url, contest_beer=cb)
