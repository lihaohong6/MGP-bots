import argparse
import itertools
import re
import sys
from typing import Optional

from pywikibot import Page, FilePage
from pywikibot.bot import SingleSiteBot
from pywikibot.pagegenerators import GeneratorFactory, PreloadingGenerator

from utils.sites import mgp, cm
from utils.utils import generate_possible_titles


class MoveImageBot(SingleSiteBot):

    def __init__(self, image_from: str, image_to: str, summary: Optional[str] = None):
        gen = GeneratorFactory(site=mgp())
        for filename in generate_possible_titles(image_from):
            gen.handle_arg(f'-search:insource:"{filename}"')
        gen1 = gen.getCombinedGenerator(preload=True)
        gen2 = PreloadingGenerator(Page(source=mgp(), title=p.title())
                                   for p in FilePage(source=cm(), title="File:" + image_from).globalusage())
        generator = itertools.chain(gen1, gen2)
        super().__init__(site=mgp(), generator=generator)
        self.image_from = image_from
        self.from_pattern = "".join("[ _]" if c == ' ' or c == '_' else c
                                    for c in re.escape(image_from).replace(r"\ ", " "))
        self.image_to = image_to
        if summary is None:
            summary = f"替换[[cm:File:{image_from}|{image_from}]]为[[cm:File:{image_to}|{image_to}]]"
        self.summary = summary
        self.processed = set()

    def treat(self, page: Page) -> None:
        if page.title() in self.processed:
            return
        if page.namespace().id == 2:
            print(page.title() + " is a user page.")
            return
        self.processed.add(page.title())
        prev = page.text
        text, _ = re.subn(self.from_pattern, self.image_to, page.text)
        self.userPut(page, prev, text, tags="Automation tool", summary=self.summary, watch="nochange")


def move_image():
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--from", dest="from", type=str, required=True)
    parser.add_argument("-t", "--to", dest="to", type=str, required=True)
    parser.add_argument("-s", "--summary", dest="summary", type=str, default=None)
    args = parser.parse_args(sys.argv[2:])
    bot = MoveImageBot(getattr(args, 'from'), args.to, args.summary)
    bot.run()
