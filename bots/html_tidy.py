from typing import Any

from pywikibot import Page
from pywikibot.bot import SingleSiteBot


class HTMLTidyBot(SingleSiteBot):
    def __init__(self, gen):
        super().__init__(generator=gen)


    def treat(self, page: Page) -> None:
        page.text
