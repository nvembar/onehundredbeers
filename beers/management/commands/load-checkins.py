from django.core.management.base import BaseCommand, CommandError
from django.db.models import Model
from django.utils import timezone
from beers.models import Beer, Player, Contest_Checkin, Contest_Beer, Contest, Contest_Player
from beers.utils.checkin import load_player_checkins
from dateutil.parser import parse
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):

    help = 'Loads checkins across contests'

    def add_arguments(self, parser):
        parser.add_argument('--player', nargs=1, help='Player')
        parser.add_argument('--contest', nargs=1, help='Contest ID')
        parser.add_argument('--after-date', nargs=1, help='After date')

    def handle(self, *args, **kwargs):
        player = None
        contest_id = None
        after_date = None
        if opts['player'] and len(opts['player']) > 0:
            player = opts['player'][0]
        if opts['contest'] and len(opts['contest']) > 0:
            try:
                contest_id = int(opts['contest'][0])
            except ValueError:
                logger.error('Error: load-checkins got a contest that was not an integer: {}'.opts['contest'][0])
                return
        if opts['after-date'] and len(opts['after-date']) > 0:
            try:
                after_date = parse(opts['after-date'][0])
            except ValueError:
                logger.error('Error: load-checkins got a malformed date: {}'.opts['after-date'][0])
                return
        players = Player.objects.all()
        if not player is None:
            players = players.filter(user__username=player)
        for p in players:
            load_player_checkins(p, from_date=after_date, contest_id=contest)
