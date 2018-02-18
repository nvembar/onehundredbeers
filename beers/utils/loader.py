"""Utility to load a contest from a CSV file"""

import csv
import logging
from beers.models import Beer, Contest, Player
from django.db import transaction

logger = logging.getLogger(__name__)

BREWERY_NAME_INDEX = 0
BEER_NAME_INDEX = 1
UNTAPPD_LINK_INDEX = 2
BEER_STATE_INDEX = 3
BEER_POINTS_INDEX = 4


@transaction.atomic
def create_contest_from_csv(name, start_date, end_date, runner, stream):
    """
    Creates a contest from a CSV stream with the given name with the given
    runner. The runner should be a Player in the G_ContestRunner group, and
    it will be added to the list of players.
    The CSV file should contain the beer list.
    """

    if not isinstance(runner, Player):
        raise TypeError("The runner must be of type Player")

    if runner.user.groups.filter(name='G_ContestRunner').count() == 0:
        raise ValueError("The runner needs to be in the contest runner group")

    contest = Contest.objects.create_contest(name=name,
                                             creator=runner,
                                             start_date=start_date,
                                             end_date=end_date)

    reader = csv.DictReader(stream,
                            fieldnames=('brewery',
                                        'name',
                                        'untappd',
                                        'state',
                                        'points'))
    is_first = True
    line = 0
    for row in reader:
        if is_first:
            is_first = False
        else:
            points = None
            try:
                points = int(row['points'])
            except ValueError as e:
                raise ValueError('Invalid point value {} on line {}'.format(row['points'], line))
            beers = Beer.objects.filter(name=name, brewery=row['brewery'])
            beer = None
            # If the beer already exists, don't recreate it
            if beers.count() == 0:
                beer = Beer.objects.create_beer(name=row['name'],
                                                brewery=row['brewery'],
                                                brewery_state=row['state'],)
                logger.info('Saving new beer %s/%s', beer.name, beer.brewery)
                beer.save()
            else:
                beer = beers.get()
                logger.info('Found beer %s/%s', beer.name, beer.brewery)
            # Add the beer we found to the new contest
            contest.add_beer(beer, point_value=points)
        line = line + 1
