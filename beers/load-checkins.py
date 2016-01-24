# This is meant to be a standalone script that goes through each player and adds all
# of teir checkins to a queue of unvalidated checkins that need to be checked by the
# contest owner
import django
import re
import logging

django.setup()

from beers.models import Player, Contest_Player, Contest, Unvalidated_Checkin
from beers.models import Contest_Checkin
import feedparser
import datetime

logger = logging.getLogger('beers')

print("__name__ = {}".format(__name__))
print("logger = {}".format(logger))

players = Player.objects.all()
re_has_loc = re.compile(r'^(.+)\s+at\s+(.+)$')
re_title = re.compile(r'^(?P<user>.+)\s+is\s+drinking\s+a(n){0,1}\s+(?P<beer>.+)\s+by\s+(?P<brewery>.+)(\s+at\s+.+){0,1}$')

for p in players:
    if p.untappd_rss:
        feed = feedparser.parse(p.untappd_rss)
        cps = Contest_Player.objects.filter(player_id=p.id)
        for cp in cps:
            contest = cp.contest
            last_date = cp.last_checkin_load
            logger.debug('User {} for {} has last load {}'.format(
                cp.player.user.username, contest.name,
                last_date))

            for c in feed.entries:
                # Example: Wed, 02 Dec 2015 00:45:37 +0000
                dt = datetime.datetime.strptime(c.published, '%a, %d %b %Y %H:%M:%S %z')
                # the checkin has to be in the contest timeframe and
                # after the last checkin from the user
                if (dt < contest.start_date or dt > contest.end_date or
                            dt <= cp.last_checkin_load):
                    logger.debug('Ignoring "{0}" as {1} is out of bounds'.format(c.title, c.published))
                    continue
                if (Unvalidated_Checkin.objects.filter(contest_player_id=cp.id,
                            untappd_checkin=c.link).count() == 0
                        or Contest_Checkin.objects.filter(contest_player_id=cp.id,
                            untappd_checkin=c.link).count() == 0):
                    if last_date is None:
                        last_date = dt
                    elif last_date < dt:
                        last_date = dt
                    lmatch = re.match(re_has_loc, c.title)
                    title = c.title
                    if lmatch:
                        title = lmatch.group(1)
                    match = re.match(re_title, title)
                    if not match:
                        logger.info("{0} did not match '{1}'".format(re_title, c.title))
                        continue
                    uv = Unvalidated_Checkin.objects.create_checkin(cp, c.title,
                            match.group('brewery').strip(),
                            match.group('beer').strip(), c.link, dt)
                    logger.info('\tAdding "{0}" to {1} for {2} with date {3}'.format(
                        uv.untappd_title, p.user.username, cp.contest.id, dt))
                    uv.save()
                else:
                    logger.debug('Ignoring "{0}" as it already exists in database'.format(c.title))
            cp.last_checkin_load = last_date
            cp.save()
