import sys

import pywikibot
from pywikibot import Page

from bots.isbn import treat_isbn, ISBN_BOT_SUMMARY
from bots.link_adjust import treat_links, LINK_ADJUST_BOT_SUMMARY
from bots.recent_changes_bot import RecentChangesBot
from utils.config import get_default_save_params


def patrol_recent_changes():
    bots = {
        'link_adjust': (treat_links, LINK_ADJUST_BOT_SUMMARY),
        'isbn': (treat_isbn, ISBN_BOT_SUMMARY)
    }
    args = sys.argv[2:]
    if len(args) > 0:
        bots = [(k, v) for k, v in bots.items() if k in args]
    pywikibot.output("Running " + ", ".join(bots.keys()))
    assert len(bots) > 0

    def treat_page(page: Page):
        if "{{施工中" in page.text:
            return
        summaries = []
        for func, summary in bots.values():
            text = func(page.text)
            if text != page.text:
                summaries.append(summary)
                page.text = text
        if len(summaries) > 0:
            page.save(summary="；".join(summaries), **get_default_save_params())

    bot = RecentChangesBot(bot_name="recent_changes")
    bot.treat = treat_page
    bot.run()
