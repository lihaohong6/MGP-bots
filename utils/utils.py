import re
import signal
import time
from typing import List, Set

import wikitextparser as wtp
from wikitextparser import Template, WikiLink

from utils.config import get_data_path
from utils.mgp import MGPPage


def process_title(s: str) -> str:
    return s.strip().replace(" ", "_").lower()


def str_equal(t1: str, t2: str) -> bool:
    return process_title(t1) == process_title(t2)


def str_contains(s1: str, s2: str) -> bool:
    return process_title(s1) in process_title(s2)


def is_empty(s: str) -> bool:
    return s is None or len(s) == 0 or s.isspace()


def find_templates(templates: List[Template], *names, loose: bool = False) -> List[Template]:
    result = []
    for t in templates:
        template_name = t.name
        if ':' in template_name and re.search("T(emplate)?:", template_name) is not None:
            template_name = template_name.split(":")[1]
        for target in names:
            if str_equal(template_name, target) or (loose and str_contains(target, template_name)):
                result.append(t)
                break
    return result


def parse_links(links: Template) -> List:
    result = []
    prefix = ""
    if str_equal(links.name, "linksplit"):
        p = links.get_arg("prefix")
        if p is not None:
            prefix = p.value
    for arg in links.arguments:
        if str_equal(arg.name, "prefix"):
            continue
        value = arg.value
        value = re.sub("<!--[\n ]*-->", "", value)
        if "{{!}}" in value:
            value = value.split("{{!}}")[0]
        result.append(prefix + value)
    return result


def count_trailing_newline(text: str) -> int:
    result = 0
    index = len(text) - 1
    while index >= 0 and text[index] == '\n':
        index -= 1
        result += 1
    return result


def throttle(throttle_time: int):
    epoch_time = time.time()
    sleep_time = throttle_time - (epoch_time - throttle.last_throttle)
    if sleep_time > 0:
        time.sleep(sleep_time)
    throttle.last_throttle = time.time()


throttle.last_throttle = 0


def get_links_in_template(page: MGPPage) -> List[str]:
    parsed = wtp.parse(page.text)
    nav_boxes = find_templates(parsed.templates, "大家族", "Navbox", loose=True)
    pages: Set[str] = set()
    for nav_box in nav_boxes:
        for link in nav_box.wikilinks:
            pages.add(link.title)
        if len(nav_box.wikilinks) == 0:
            # {{tl|links}} is probably used
            links = find_templates(nav_box.templates, "links", "大家族内容行", "linksplit")
            for t in links:
                for page in parse_links(t):
                    pages.add(page)
    return list(pages)


def get_continue_page(file_name: str) -> str:
    path = get_data_path().joinpath(file_name)
    if path.exists():
        with open(path, "r") as f:
            return f.read()
    return '!'


def save_continue_page(file_name: str, page_name: str):
    path = get_data_path().joinpath(file_name)
    original = signal.signal(signal.SIGINT, signal.SIG_IGN)
    with open(path, "w") as f:
        f.write(page_name)
    signal.signal(signal.SIGINT, original)


def get_categories(parsed: wtp.WikiText) -> List[WikiLink]:
    """
    Retrieve all categories apparent in the text. Note that this function does
    not resolve categories added by transcluding templates. Useful when the user
    does not want to send an extra request to the server to expand a page for all
    categories.
    :param text: wikitext to be analyzed
    :return: list of categories
    """
    result = []
    for link in parsed.wikilinks:
        res = re.search("(category|cat|分类):", link.title, re.I)
        if res is not None and res.start() == 0:
            result.append(link)
    return result
