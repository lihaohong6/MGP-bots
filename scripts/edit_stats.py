from datetime import timedelta, timezone

from pywikibot import Timestamp

from utils.sites import mgp
from utils.utils import parse_time

site = mgp()
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

