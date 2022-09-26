import datetime
from abc import ABC

import pywikibot
from pywikibot import APISite, Page, Timestamp
from pywikibot.bot import SingleSiteBot
from pywikibot.pagegenerators import PreloadingGenerator

from utils.config import get_rate_limit, get_data_path
from datetime import timezone, datetime, timedelta


def filter_recent_changes(resume_id: int, recent_changes_generator):
    existing_titles = set()
    for item in recent_changes_generator:
        if resume_id is None:
            pywikibot.error("Don't know where to resume. Reading the past 5000 changes")
            resume_id = item['rcid'] - 5000
        page_title = item['title']
        if page_title in existing_titles:
            continue
        if item['rcid'] < resume_id:
            break
        existing_titles.add(page_title)
        yield item


class RecentChangesBot(SingleSiteBot, ABC):
    from utils.sites import mgp

    def __init__(self, bot_name: str, resume_id: int = None, site: APISite = mgp, group_size: int = get_rate_limit(),
                 ns: str = "0", time_offset: int = -2, **kwargs):
        super(RecentChangesBot, self).__init__(site=site, **kwargs)
        self.group_size = group_size
        self.resume_file = get_data_path().joinpath(bot_name + "_resume.txt")
        # TODO: create a separate resume file for new pages
        if self.resume_file.exists() and resume_id is None:
            try:
                with open(self.resume_file, "r") as f:
                    resume_id = int(f.read())
            except Exception as e:
                pywikibot.error(e)
        # use current time
        cur_time = datetime.now(tz=timezone(offset=timedelta(hours=0), name="UTC"))
        # compute recent changes delay based on offset
        rc_time = cur_time + timedelta(hours=time_offset)
        time_start = Timestamp(rc_time.year, rc_time.month, rc_time.day,
                               rc_time.hour, rc_time.minute, rc_time.second,
                               tzinfo=rc_time.tzinfo)
        self.gen = filter_recent_changes(resume_id,
                                         site.recentchanges(namespaces=ns, bot=None, redirect=False,
                                                            changetype='edit|new', start=time_start, top_only=True))
        self._start_ts = pywikibot.Timestamp.now()

    def run(self) -> None:
        self.setup()
        changes = list(self.gen)
        changes.reverse()
        pywikibot.output(f"Patrolling {len(changes)} recently changed pages")
        if len(changes) > 0:
            pywikibot.output(f"Examining pages with rcid from {changes[0]['rcid']} to {changes[-1]['rcid']}")
        else:
            pywikibot.output("No pages recently changed.")
            self.exit()
            return
        gen = PreloadingGenerator((Page(source=self.site, title=item['title']) for item in changes),
                                  groupsize=self.group_size)
        for index, page in enumerate(gen):
            try:
                self.treat(page)
            except Exception as e:
                print(e)
            with open(self.resume_file, "w") as f:
                f.write(str(changes[index]['rcid']))

        last_entry = changes[-1]
        pywikibot.output(f"Last page is titled {last_entry['title']} with rcid {last_entry['rcid']} "
                         f"modified on {last_entry['timestamp']}")
        self.exit()
