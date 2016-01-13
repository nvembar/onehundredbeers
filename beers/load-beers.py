# This loads up data beer data into the database

import django
import csv
import sys
import argparse

django.setup()

from beers.models import Beer, Contest, Contest_Beer

parser = argparse.ArgumentParser(description='Load beers into database')
parser.add_argument('--contest-id', '-c', type=int, action='append',
            help='Contest ID to add beers to', dest='contest_ids')
parser.add_argument('filename', nargs='?', default='<>',
                    help='CSV file to be consumed (no file will read from stdin)')

args = parser.parse_args()

# There's got to be a better way....
try:
    contests = [Contest.objects.get(id=contest_id) for contest_id in args.contest_ids]
except Contest.DoesNotExist as e:
    print('Could not find contest {0}'.format(e))
    exit(1)

with open(args.filename) if args.filename != '<>' else sys.stdin as csvfile:
    reader = csv.reader(csvfile)
    is_first = True
    for row in reader:
        try:
            if is_first:
                is_first = False
            else:
                # The order is Style, Beer, Brewery, City, State
                beers = Beer.objects.filter(name=row[1], brewery=row[2])[:1]
                beer = None
                if len(beers) is 0:
                    beer = Beer.objects.create_beer(name=row[1],
                                                brewery=row[2],
                                                style=row[0],
                                                brewery_city=row[3],
                                                brewery_state=row[4])
                    print('Saving new beer {0}/{1}'.format(beer.name, beer.brewery))
                    beer.save()
                else:
                    beer = beers[0]
                    print('Found beer {0}/{1}'.format(beer.name, beer.brewery))
                contest_beers = [Contest.objects.add_beer(c, beer) for c in contests]
                for cb in contest_beers:
                    print('Adding {0}/{1} to contest {2}'.format(beer.name,
                            beer.brewery, cb.contest.name))
                    cb.save()
        except BaseException as e:
            print("Line: '{0}'".format(row))
            print(e)
            raise e
