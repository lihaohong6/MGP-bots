from abc import ABC

import pywikibot
from pywikibot import APISite, Page
from pywikibot.bot import SingleSiteBot
from pywikibot.pagegenerators import PreloadingGenerator

from utils.config import get_data_path
from utils.sites import mgp


def filter_recent_changes(resume_id: int, recent_changes_generator):
    for item in recent_changes_generator:
        if resume_id is None:
            pywikibot.error("Don't know where to resume. Reading the past 5000 changes")
            resume_id = item['rcid'] - 5000
        if item['rcid'] < resume_id:
            break
        yield item


class RecentChangesBot(SingleSiteBot, ABC):
    def __init__(self, bot_name: str, resume_id: int = None, site: APISite = mgp, group_size: int = 50,
                 ns: str = "0", **kwargs):
        super(RecentChangesBot, self).__init__(site=site, **kwargs)
        self.group_size = group_size
        self.resume_file = get_data_path().joinpath(bot_name + "_resume.txt")
        if self.resume_file.exists() and resume_id is None:
            try:
                resume_id = int(open(self.resume_file, "r").read())
            except Exception as e:
                pywikibot.error(e)
        self.gen = filter_recent_changes(resume_id,
                                         site.recentchanges(namespaces=ns, bot=False, redirect=False))
        self._start_ts = pywikibot.Timestamp.now()

    def run(self) -> None:
        self.setup()
        changes = list(self.gen)
        changes.reverse()
        pywikibot.output(f"Patrolling {len(changes)} recent changes")
        gen = PreloadingGenerator((Page(source=self.site, title=item['title']) for item in changes),
                                  groupsize=self.group_size)
        for index, page in enumerate(gen):
            try:
                self.treat(page)
            except Exception as e:
                print(e)
            with open(self.resume_file, "w") as f:
                f.write(str(changes[index]['rcid']))

        self.exit()
