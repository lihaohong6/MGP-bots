from typing import Any

from pywikibot import Page
from pywikibot.bot import SingleSiteBot

from utils.config import get_default_save_params


def treat_boilerplate(text: str) -> str:
    pass


BOILERPLATE_BOT_SUMMARY = "去除预加载"


class BoilerplateBot(SingleSiteBot):
    def treat(self, page: Page) -> None:
        text = treat_boilerplate(page.text)
        if text != page.text:
            page.text = text
            page.save(summary=BOILERPLATE_BOT_SUMMARY, **get_default_save_params())
