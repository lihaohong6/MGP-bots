import re
from typing import Set

import wikitextparser as wtp
from re import Match

from pywikibot import Page
from pywikibot.bot import SingleSiteBot

from utils.config import get_default_save_params
from utils.utils import search_pages

ISBN_BOT_SUMMARY = "使用[[T:ISBN]]"


def sub_isbn(text: str, blacklist: Set[str]) -> str:
    def replace(m: Match) -> str:
        raw = m.group(0)
        lower = raw.lower()
        # skip images
        if ".jp" in lower or ".png" in lower or ".webp" in lower or ".gif" in lower:
            return raw
        isbn = m.group(1)
        # skip isbn in wiki links and urls
        for forbid in blacklist:
            if isbn in forbid:
                return raw
        extra1 = extra2 = ""
        # keep ISBN: and ISBN：
        if "ISBN:" == raw[:5] or "ISBN：" == raw[:5]:
            extra1 = raw[:5]
            extra2 = "|" + isbn
        return extra1 + "{{ISBN|" + isbn + extra2 + "}}" + m.group(2)

    return re.sub(r"(?<![/.])ISBN[ :：]?([\d-]{10,20}[xX]?)(?<!-)(.*)",
                  replace,
                  text,
                  re.IGNORECASE)


def treat_isbn(text: str) -> str:
    blacklist = set()
    parsed = wtp.parse(text)
    for link in parsed.wikilinks:
        blacklist.add(link.string)
    for link in parsed.external_links:
        blacklist.add(link.string)
    for link in re.findall(r"\[https?://[^]]+]", text):
        blacklist.add(link)
    for link in re.findall("https?://" + r"""(((?![ 　\]{}<|\n])[ -~])*)""", text):
        blacklist.add(link[0])
    while True:
        # re.sub sometimes doesn't work for multiple isbn,
        # so apply sub repeatedly
        res = sub_isbn(text, blacklist)
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
    bot = IsbnBot(site=mgp(), generator=gen)
    bot.run()
