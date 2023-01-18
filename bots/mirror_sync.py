import pickle
import threading
from pathlib import Path
from time import sleep

import pywikibot
from pywikibot import Page
from pywikibot.bot import SingleSiteBot
from pywikibot.pagegenerators import GeneratorFactory
from pywikibot.site import Namespace

from bots.recent_changes_bot import RecentChangesBot
from utils.sites import mirror


s = mirror()
page_folder = Path("sync_pages")


def get_white_list():
    white_list = set()
    gen = GeneratorFactory(site=s)
    gen.handle_arg("-catr:同步白名单")
    gen = gen.getCombinedGenerator(preload=False)
    for p in gen:
        white_list.add(p.title(with_ns=True))
    return white_list


class RCDownloadBot(RecentChangesBot):
    def __init__(self):
        super().__init__("mirror_sync",
                         ns=[0, 'Template', '萌娘百科', 'Module', 'Help', 'Category'],
                         delay=0)
        self.white_list = get_white_list()

    def treat(self, page: Page) -> None:
        change = self.current_change
        if change['type'] == 'log' and change['logaction'] == 'move' and change['logparams']['target_ns'] != 2:
            page.move(change['logparams']['target_title'])
        title = page.title(with_ns=True)
        if title in self.white_list:
            return
        pywikibot.output("Writing file for page " + title)
        page_id = page.pageid
        page_path = page_folder.joinpath(str(page_id) + ".pickle")
        with open(page_path, "wb") as f:
            pickle.dump({'title': title, 'text': page.text}, f)


def process_file(f):
    obj = pickle.load(open(f, "rb"))
    p = Page(source=s, title=obj['title'])
    p.text = obj['text']
    p.save(summary="搬运/同步自萌娘百科的同名条目", watch='nochange', botflag=True, force=True)
    f.unlink()


def mirror_sync():
    pywikibot.output("Syncing pages from mgp with mirror.")
    page_folder.mkdir(exist_ok=True)
    bot = RCDownloadBot()
    bot.run()
    THREAD_LIMIT = 3
    current_threads = []
    for f in page_folder.glob("*.pickle"):
        if not f.name[0].isdigit():
            print("Skipping " + f.name)
            return
        while len(current_threads) >= THREAD_LIMIT:
            sleep(0.1)
            current_threads = [t for t in current_threads if t.is_alive()]
        t = threading.Thread(target=lambda: process_file(f))
        t.start()
        current_threads.append(t)


if __name__ == "__main__":
    mirror_sync()
