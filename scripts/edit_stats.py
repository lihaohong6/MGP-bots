from datetime import timedelta, datetime, date, timezone

from pywikibot import Timestamp

import init_script
from utils.sites import mgp, mirror
from utils.utils import parse_time

site = mgp()
cst = timezone(timedelta(hours=8), 'CST')
now = Timestamp.now().astimezone(timezone.utc)
changes = site.recentchanges(end=now + timedelta(hours=-24), start=now, bot=False)
changes = list(changes)
timestamps = [parse_time(c['timestamp'], cst=True)
              for c in changes]
print(timestamps[0], timestamps[-1])
buckets = dict((i, 0) for i in range(24))
for t in timestamps:
    buckets[t.hour] += 1
print("\n".join(f"{hour}: {edits}" for hour, edits in buckets.items()))

