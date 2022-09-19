import re
from re import Match

from pywikibot import Page
from pywikibot.bot import SingleSiteBot

from utils.config import get_default_save_params
from utils.utils import search_pages

ISBN_BOT_SUMMARY = "使用[[T:ISBN]]"


def sub_isbn(text: str) -> str:
    def replace(m: Match) -> str:
        raw = m.group(0)
        lower = raw.lower()
        if ".jp" in lower or ".png" in lower or ".webp" in lower or ".gif" in lower:
            return raw
        extra1 = extra2 = ""
        if "ISBN:" == raw[:5] or "ISBN：" == raw[:5]:
            extra1 = raw[:5]
            extra2 = "|" + m.group(1)
        return extra1 + "{{ISBN|" + m.group(1) + extra2 + "}}" + m.group(2)

    return re.sub(r"ISBN[ :：]?([\d-]{10,20}X?)(.*)",
                  replace,
                  text,
                  re.IGNORECASE)


def treat_isbn(text: str) -> str:
    while True:
        res = sub_isbn(text)
        if res == text:
            return res
        text = res


class IsbnBot(SingleSiteBot):

    def treat(self, page: Page):
        text = treat_isbn(page.text)
        if text != page.text:
            page.text = text
            page.save(summary=ISBN_BOT_SUMMARY, **get_default_save_params())


def isbn_adjust():
    from utils.sites import mgp
    gen = search_pages("ISBN", preload=True)
    bot = IsbnBot(site=mgp, generator=gen)
    bot.run()
