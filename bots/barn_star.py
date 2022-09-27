import pickle
from pathlib import Path

import pywikibot
from pywikibot import Page
from pywikibot.bot import SingleSiteBot

from utils.contributions import write_contributions_to_file
from utils.logger import get_logger
from utils.mgp import get_page
from utils.utils import get_links_in_template, count_trailing_newline


class BarnStarBot(SingleSiteBot):

    def __init__(self, generator, title, body):
        super().__init__(generator=generator)
        self.title = title
        self.body = body
        self.message = "== {} ==\n\n{}".format(title, body)

    def treat(self, page: Page) -> None:
        if page.exists():
            old_text = page.text
        else:
            old_text = ""
        existing_newlines = count_trailing_newline(old_text)
        self.userPut(page,
                     old_text,
                     old_text + max(0, 2 - existing_newlines) * "\n" + self.message,
                     summary=self.title,
                     minor=False,
                     tags="Automation tool")


def auto_star(template_name: str, print_contributions: bool = True, send_stars: int = -1, title: str = "",
              body: str = ""):
    file_name = Path("data/{}.pickle".format(template_name))
    if not file_name.exists():
        write_contributions_to_file(get_links_in_template(get_page('T' + template_name)), file_name)
    with open(file_name, "rb") as f:
        contributions = pickle.load(f)
    contrib_list = list(sorted(contributions.items(), key=lambda t: t[1][0], reverse=True))
    if print_contributions:
        get_logger().info("\n".join(str(c) for c in contrib_list))
    if send_stars >= 0:
        targets = (Page(pywikibot.Site(), "User_talk:" + person[0])
                   for person in contrib_list if person[1][0] > send_stars)
        bot = BarnStarBot(targets, title=title, body=body)
        bot.run()
