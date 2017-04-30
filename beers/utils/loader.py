from beers.models import Beer, Contest_Beer, Contest, Contest_Player, Player
import csv
import logging

logger = logging.getLogger(__name__)

BREWERY_NAME_INDEX=0
BEER_NAME_INDEX=1
UNTAPPD_LINK_INDEX=2
BEER_STATE_INDEX=3
BEER_POINTS_INDEX=4


def create_contest_from_csv(name, start_date, end_date, runner, stream):
    """
    Creates a contest from a CSV stream with the given name with the given runner.
    The runner should be a Player in the G_ContestRunner group, and it will be added
    to the list of players.
    The CSV file should contain the beer list.
    """

    if not isinstance(runner, Player):
        raise TypeError("The runner must be of type Player")

    if runner.user.groups.filter(name='G_ContestRunner').count() == 0:
        raise ValueError("The runner needs to be in the contest runner group")

    contest = Contest.objects.create_contest(name=name,
        creator=runner,
        start_date=start_date,
        end_date=end_date,
    )
    cp = Contest_Player.objects.link(contest=contest, player=runner)

    reader = csv.DictReader(stream, fieldnames=('brewery', 'name', 'untappd', 'state', 'points'))
    is_first = True
    line = 0
    for row in reader:
        if is_first:
            is_first = False
        else:
            name = row['name']
            brewery = row['brewery']
            state = row['state']
            points = None
            try:
                points = int(row['points'])
            except ValueError as e:
                raise ValueError('Invalid point value {} on line {}'.format(row['points'], line))
            link = row['untappd']
            beers = Beer.objects.filter(name=name, brewery=brewery)
            beer = None
            # If the beer already exists, don't recreate it
            if beers.count() == 0:
                beer = Beer.objects.create_beer(name=name,
                                            brewery=brewery,
                                            brewery_state=state,)
                logger.info('Saving new beer %s/%s', beer.name, beer.brewery)
                beer.save()
            else:
                beer = beers.get()
                logger.info('Found beer %s/%s'.format(beer.name, beer.brewery))
            # Add the beer we found to the new contest
            cb = Contest.objects.add_beer(contest, beer, point_value=points)
            cb.save()
        line = line + 1
