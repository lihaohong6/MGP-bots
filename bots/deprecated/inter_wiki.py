from typing import List

from pywikibot import Page
from pywikibot.exceptions import SiteDefinitionError
from pywikibot.pagegenerators import AllpagesPageGenerator

import wikitextparser as wtp
from wikitextparser import WikiLink

from utils.config import get_lang_map
from utils.logger import get_logger
from utils.utils import count_trailing_newline, is_empty, get_continue_page, save_continue_page


def get_lang_links(page: Page, lang_filter: str) -> List[WikiLink]:
    # FIXME: use api to batch request language links
    try:
        expanded = page.expand_text()
    except SiteDefinitionError as e:
        get_logger().warning("Page " + page.title() + " cannot be expanded.")
        expanded = page.text
    parsed = wtp.parse(expanded)
    links: List[WikiLink] = parsed.wikilinks
    return [link for link in links if lang_filter in link.title.lower() and is_empty(link.text)]


class InterWikiBot:
    def __init__(self, source: str, target: str):
        self.source = source
        self.target = target
        self.source_site = get_lang_map()[source]
        self.target_site = get_lang_map()[target]
        self.target_site.login()

    def treat_page(self, page):
        target_site = self.target_site
        source_lang = self.source + ":"
        target_lang = self.target + ":"
        source_title = page.title(as_link=True, allow_interwiki=False).lstrip('[').rstrip(']')
        target = get_lang_links(page, target_lang)
        if len(target) == 0:
            get_logger().info(page.title() + " has no inter wiki link")
            return
        if len(target) > 1:
            get_logger().error(page.title() + " contains too many links: " + str(target))
            return
        target_title = target[0].title[target[0].title.find(':') + 1:]
        page = Page(target_site, target_title)
        if not page.exists():
            get_logger().error("Page " + page.title() + " does not exist on " + self.target)
            return
        if len(get_lang_links(page, source_lang)) > 0:
            get_logger().info("Page " + page.title() + " already contains inter wiki link.")
            return
        if page.isRedirectPage():
            get_logger().warning("Page " + page.title() + " is a redirect page")
            return
        newline = count_trailing_newline(page.text)
        page.text += "\n" * max(0, 2 - newline) + "[[" + source_lang + source_title + "]]"
        get_logger().info(page.title() + " -> " + source_title)
        page.save(summary="添加" + self.source + "站链接", minor=True,
                  tags="Automation tool", watch="nochange")

    def run(self):
        save_file = "inter_wiki.txt"
        gen = AllpagesPageGenerator(start=get_continue_page(save_file),
                                    namespace=0, site=self.source_site)
        for page in gen:
            self.treat_page(page)
            save_continue_page(save_file, page.title(as_link=True, allow_interwiki=False).lstrip('[').rstrip(']'))
