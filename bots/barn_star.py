import pickle
from pathlib import Path
from typing import Tuple, List, Dict

import pywikibot
from pywikibot import Page
from pywikibot.bot import SingleSiteBot
from pywikibot.page import Revision
from pywikibot.site import Namespace

from utils.logger import get_logger
from utils.mgp import get_page
from utils.utils import get_links_in_template, count_trailing_newline

ContributionInfo = Tuple[int, List[str]]


def process_revision(old_info: ContributionInfo, revision, byte_diff: int, page_name: str) -> ContributionInfo:
    tags = revision['tags']
    if "mw-undo" in tags:
        byte_diff = 0
    prev_list = old_info[1]
    if page_name not in prev_list:
        prev_list.append(page_name)
    return old_info[0] + max(0, byte_diff), prev_list


def process_page(contributions, page_name):
    page = get_page(page_name)
    if page.exists() and page.namespace().id == 0:
        revisions: List[Revision] = list(page.revisions(reverse=True))
        prev_bytes = 0
        for revision in revisions:
            user = revision['user']
            byte_count = revision['size']
            byte_diff = prev_bytes - byte_count
            contributions[user] = process_revision(contributions.get(user, (0, [])),
                                                   revision,
                                                   byte_diff,
                                                   page_name)
            prev_bytes = byte_count


def write_contributions_to_file(template_name: str, temp_file: Path):
    pages = get_links_in_template(get_page(template_name))
    contributions: Dict[str, Tuple[int, List[str]]] = dict()
    for index, page_name in enumerate(pages):
        process_page(contributions, page_name)
        get_logger().info(f"{index}/{len(pages)} ")
    with open(temp_file, "wb") as f:
        pickle.dump(contributions, f, protocol=pickle.HIGHEST_PROTOCOL)


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
        write_contributions_to_file("T:" + template_name, file_name)
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
