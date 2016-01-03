# This is meant to be a standalone script that goes through each player and adds all
# of teir checkins to a queue of unvalidated checkins that need to be checked by the
# contest owner
import django
import re

django.setup()

from beers.models import Player, Contest_Player, Contest, Unvalidated_Checkin
import feedparser
import datetime

players = Player.objects.all()
re_has_loc = re.compile(r'^(.+) at (.+)$')
re_title = re.compile(r'^(?P<user>.+) is drinking a(n){0,1}\s+(?P<beer>.+)\s+by\s+(?P<brewery>.+)( at .+){0,1}$')

for p in players:
    if p.untappd_rss:
        feed = feedparser.parse(p.untappd_rss)
        cps = Contest_Player.objects.filter(player_id=p.id)
        for cp in cps:
            for c in feed.entries:
                if Unvalidated_Checkin.objects.filter(contest_player_id=cp.id, untappd_checkin=c.link).count() is 0:
                    # Example: Wed, 02 Dec 2015 00:45:37 +0000
                    # Get rid of the last set of characters
                    dt = datetime.datetime.strptime(c.published, '%a, %d %b %Y %H:%M:%S %z')
                    lmatch = re.match(re_has_loc, c.title)
                    title = c.title
                    if lmatch:
                        print('Found a location: {0}'.format(c.title))
                        title = lmatch.group(1)
                    match = re.match(re_title, title)
                    if not match:
                        print("{0} did not match '{1}'".format(re_title, c.title))
                        continue
                    uv = Unvalidated_Checkin.objects.create_checkin(cp, c.title,
                            match.group('brewery'), match.group('beer'), c.link, dt)
                    print('\tAdding "{0}" to {1} for {2}'.format(uv.untappd_title, p.user.username, cp.contest.id))
                    uv.save()
