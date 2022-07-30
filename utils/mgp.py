import webbrowser
from typing import Optional

import pywikibot as pwb
import wikitextparser

DEFAULT_SITE = pwb.Site()
MGP_BASE_URL = "https://zh.moegirl.org.cn/"


class MGPPage(pwb.Page):
    @property
    def name(self):
        return self.title(underscore=True)

    @property
    def link(self):
        return MGP_BASE_URL + self.title(as_url=True)

    def open_in_browser(self):
        webbrowser.open(self.link)


def get_page(title: str, resolve_redirect: bool = True) -> Optional[MGPPage]:
    page = MGPPage(DEFAULT_SITE, title)
    if not page.exists() or not resolve_redirect:
        return page
    t = page.text.strip()
    if t[0] == '#':
        parsed = wikitextparser.parse(t)
        links = parsed.wikilinks
        if len(links) == 1:
            return get_page(links[0].title)
    return page
