import re
import webbrowser
from threading import Thread
from typing import Any

from pywikibot import Page
from pywikibot.bot import SingleSiteBot
from pywikibot.pagegenerators import GeneratorFactory
from pywikibot.tools.itertools import itergroup
from wikitextparser import parse

from utils.sites import mgp
from utils.utils import find_templates
from mgp_common.video import video_from_site, VideoSite

TOP_PATTERN = re.compile(r"{{ *vocaloid(..)?..曲[題题][头頭]", re.IGNORECASE)
NICO_PATTERN = re.compile(r"{{ *niconicocount *\| *id *= *([^}]+) *}}", re.IGNORECASE)


def process_page_group(pages):
    for p in pages:
        try:
            if re.search(TOP_PATTERN, p.text) is not None:
                continue
            nico_counts = re.findall(NICO_PATTERN, p.text)
            for nico_id in nico_counts:
                video = video_from_site(VideoSite.NICO_NICO, nico_id)
                if video is None:
                    continue
                if video.views >= 100000:
                    print(p.title())
                    break
        except Exception as e:
            print(e)


def get_page_list():
    gen = GeneratorFactory(site=mgp())
    # gen.handle_args(["-file:data/pages.txt"])
    gen.handle_args(["-ns:0", "-cat:使用VOCALOID的歌曲"])
    pages = gen.getCombinedGenerator(preload=True)
    threads = []
    for page_group in itergroup(pages, 50):
        t = Thread(target=process_page_group(page_group))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()


class BatchAddBot(SingleSiteBot):
    def treat(self, page: Page) -> None:
        setattr(page, "_bot_may_edit", True)
        new_text = "{{VOCALOID殿堂曲题头}}\n" + page.text
        webbrowser.open(page.full_url())

        self.userPut(page, page.text, new_text, tags="Automation tool",
                     summary="已达成殿堂", asynchronous=True)

    def __init__(self):
        gen = GeneratorFactory(site=mgp())
        gen.handle_arg("-file:data/pages.txt")
        super(BatchAddBot, self).__init__(site=mgp(),
                                          generator=gen.getCombinedGenerator(preload=True))


def main():
    # get_page_list()
    bot = BatchAddBot()
    bot.run()


if __name__ == "__main__":
    main()
