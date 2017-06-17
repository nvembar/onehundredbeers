from beers.models import Player, Contest_Player, Contest, Unvalidated_Checkin, Contest_Checkin, Brewery, Contest_Brewery
from django.db import transaction
import feedparser
import datetime
import re
import logging

logger = logging.getLogger(__name__)

def load_player_checkins(p, contest_id=None, from_date=None):
    """
    Loads a players checkins, potentially after the from_date. If from_date
    is provided, then it loads anything after that date within a contest.
    Otherwise, it loads based on the last checkin that was logged.
    """

    re_has_loc = re.compile(r'^(.+)\s+at\s+(.+)$')
    re_title = re.compile(r'^(?P<user>.+)\s+is\s+drinking\s+a(n){0,1}\s+(?P<beer>.+)\s+by\s+(?P<brewery>.+)(\s+at\s+.+){0,1}$')

    logger.info("Trying to print")
    logger.debug('Parsing "{}" for player {}'.format(p.untappd_rss, p.user.username))
    if p.untappd_rss:
        feed = feedparser.parse(p.untappd_rss)
        logger.debug('Got {} entries'.format(len(feed.entries)))
        cps = None
        if contest_id is None:
            cps = Contest_Player.objects.filter(player=p)
        else:
            cps = Contest_Player.objects.filter(contest_id=contest_id, player=p)
        for cp in cps:
            contest = cp.contest
            # after_date is set from from_date so that in case after_date changes
            # across contests if from_date is not set
            after_date = from_date
            if after_date is None:
                after_date = cp.last_checkin_load
            last_date = after_date
            logger.debug('User {} for {} has last load {}'.format(
                cp.player.user.username, contest.name,
                cp.last_checkin_load))

            for c in feed.entries:
                # Example: Wed, 02 Dec 2015 00:45:37 +0000
                dt = datetime.datetime.strptime(c.published, '%a, %d %b %Y %H:%M:%S %z')
                # the checkin has to be in the contest timeframe and
                # after the last checkin from the user
                if (dt < contest.start_date or dt > contest.end_date or dt <= after_date):
                    logger.debug('Ignoring "{0}" as {1} is out of bounds'.format(c.title, c.published))
                    continue
                if (Unvalidated_Checkin.objects.filter(contest_player_id=cp.id,
                            untappd_checkin=c.link).count() == 0
                        and Contest_Checkin.objects.filter(contest_player_id=cp.id,
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


@transaction.atomic
def checkin_brewery(uv_checkin, contest_brewery, save_checkin=False):
    """
    Checks in a brewery from an unvalidated checkin for a user.

    save_checkin=True will prevent the unvalidated checkin from being deleted
    """
    cp = uv_checkin.contest_player
    checkins = Contest_Checkin.objects.filter(contest_player=cp,
                                    contest_brewery=contest_brewery,)
    checkin = None
    if checkins.count() == 0:
        checkin = Contest_Checkin.objects.create_brewery_checkin(
                contest_player=cp, contest_brewery=contest_brewery,
                checkin_time=uv_checkin.untappd_checkin_date,
                untappd_checkin=uv_checkin.untappd_checkin,
                )
        cp.total_points = cp.total_points + contest_brewery.point_value
        cp.brewery_points = cp.brewery_points + contest_brewery.point_value
    cp.last_checkin_date = uv_checkin.untappd_checkin_date
    cp.last_checkin_brewery = uv_checkin.brewery
    cp.last_checkin_beer = None
    cp.save()
    if not save_checkin:
        uv_checkin.delete()
    return checkin
