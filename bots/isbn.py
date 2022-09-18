import re

from pywikibot import Page
from pywikibot.bot import SingleSiteBot

from utils.utils import search_pages

ISBN_BOT_SUMMARY = "使用[[T:ISBN]]"


def treat_isbn(text: str) -> str:
    return re.sub(r"ISBN ?([\d-]{7,20}X?)",
                  r"{{ISBN|\1}}",
                  text,
                  re.IGNORECASE)


class IsbnBot(SingleSiteBot):

    def treat(self, page: Page):
        text = treat_isbn(page.text)
        if text != page.text:
            page.text = text
            page.save(summary=ISBN_BOT_SUMMARY, minor=True, botflag=True,
                      watch="nochange", tags="Bot")


def isbn_adjust():
    from utils.sites import mgp
    gen = search_pages("ISBN", preload=True)
    bot = IsbnBot(site=mgp, generator=gen)
    bot.run()
