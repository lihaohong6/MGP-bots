import sys
from argparse import ArgumentParser

import pywikibot
from pywikibot import Page

from bots.boilerplate import treat_boilerplate, BOILERPLATE_BOT_SUMMARY
from bots.isbn import treat_isbn, ISBN_BOT_SUMMARY
from bots.link_adjust import treat_links, LINK_ADJUST_BOT_SUMMARY
from bots.recent_changes_bot import RecentChangesBot
from utils.config import get_default_save_params


def patrol_recent_changes():
    bots = {
        'link_adjust': (treat_links, LINK_ADJUST_BOT_SUMMARY),
        'isbn': (treat_isbn, ISBN_BOT_SUMMARY),
        'boilerplate': (treat_boilerplate, BOILERPLATE_BOT_SUMMARY)
    }
    p = ArgumentParser()
    p.add_argument("-ns", "--namespace", dest="namespace", default="0", type=str)
    p.add_argument("-d", "--delay", dest="delay", default=2, type=int)
    p.add_argument("-n", "--name", dest="name", default="recent_changes", type=str)
    p.add_argument("bots", nargs='*', default=bots.keys())
    args = p.parse_args(sys.argv[2:])
    bots = dict((k, v) for k, v in bots.items() if k in args.bots)
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

    bot = RecentChangesBot(bot_name=args.name, ns=args.namespace, delay=-args.delay)
    bot.treat = treat_page
    bot.run()
