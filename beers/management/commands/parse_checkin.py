import argparse
from django.core.management.base import BaseCommand, CommandError
from beers.utils.untappd import parse_checkin, parse_beer, parse_brewery


class Command(BaseCommand):
    """Parses a Untappd web page"""

    help = 'Pulls a checkin, beer, or brewery from Untappd'

    def add_arguments(self, parser):
        parser.add_argument('type', nargs=1, choices=['beer', 'brewery', 'checkin'])
        parser.add_argument('url', nargs=1)

    def handle(self, *args, **opts):
        print("BEGIN --{}--".format(opts['url'][0]))
        result = None
        if opts['type'][0] == 'checkin':
            result = parse_checkin(opts['url'][0])
        elif opts['type'][0] == 'beer':
            result = parse_beer(opts['url'][0])
        elif opts['type'][0] == 'brewery':
            result = parse_brewery(opts['url'][0])
        print(result)
        print("END   --{}--".format(opts['url'][0]))
