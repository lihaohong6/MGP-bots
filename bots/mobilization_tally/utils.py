from datetime import datetime

import wikitextparser as wtp
from pywikibot import APISite

from utils.utils import find_templates

site: APISite


def get_site() -> APISite:
    return site


def set_site(s) -> None:
    global site
    site = s


def username_to_section_title(username: str) -> str:
    return "-{[[U:" + username + "|" + username + "]]}-"


def adjust(num: float):
    return round(num, 2)


def count_bytes_simple(text: str) -> int:
    return len(text.encode('utf-8'))


def count_bytes(text: str) -> int:
    initial = count_bytes_simple(text)
    parsed = wtp.parse(text)
    templates = ['Producer_Song', 'Album Infobox', 'Tracklist']
    subtract = []
    for t in templates:
        template_bytes = 0
        for found in find_templates(parsed.templates, t):
            template_bytes += count_bytes_simple(str(found))
        subtract.append(template_bytes)
    return round(initial - sum(subtract) / 4)