import re
import signal
import time
import urllib.parse
from datetime import datetime, timedelta, timezone
from typing import List, Set, Iterable

import wikitextparser as wtp
from pywikibot import Page, Site
from pywikibot.pagegenerators import GeneratorFactory, PreloadingGenerator
from pywikibot.tools import deprecated
from wikitextparser import Template, WikiLink

from utils.config import get_data_path, get_rate_limit
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
        if ':' in template_name and re.search("[Tt](emplate)?:", template_name) is not None:
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
    while index >= 0 and text[index].isspace():
        index -= 1
        result += 1 if text[index] == '\n' else 0
    return result


def adjust_trailing_newline(text: str, target_count: int = 2) -> str:
    return text.rstrip() + "\n" * target_count


def throttle(throttle_time: int):
    epoch_time = time.time()
    sleep_time = throttle_time - (epoch_time - throttle.last_throttle)
    if sleep_time > 0:
        time.sleep(sleep_time)
    throttle.last_throttle = time.time()


throttle.last_throttle = 0


def get_links_in_template(page: Page) -> List[str]:
    parsed = wtp.parse(page.text)
    tags = parsed.get_tags("noinclude")
    for t in tags:
        t.string = ""
    text = parsed.string
    parsed = wtp.parse(page.site.expand_text(text))
    result = []
    for link in parsed.wikilinks:
        result.append(link.title)
    return result


def get_links_in_template_deprecated(page: Page) -> List[str]:
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
        with open(path, "r", encoding="utf-8") as f:
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
    not resolve categories added by transcluding template_names. Useful when the user
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


def get_page_list(file_name: str, factory: Iterable[Page], cont: str = None, site=None) -> Iterable[Page]:
    path = get_data_path().joinpath(file_name)
    if not path.exists():
        pages = list(factory)
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(page.title() for page in pages))
    if cont is not None and cont != '!':
        with open(path, 'r', encoding="utf-8") as f:
            pages = f.read().split("\n")
        for index, page_name in enumerate(pages):
            if page_name == cont:
                path = get_data_path().joinpath("temp_page_list.txt")
                with open(path, 'w', encoding="utf-8") as f:
                    f.write("\n".join(pages[index + 1:]))
                break
    gen = GeneratorFactory(site=site)
    gen.handle_arg("-file:" + str(path.absolute()))
    return gen.getCombinedGenerator(preload=True)


def get_commons_links(text: str) -> List[str]:
    links = re.findall(r"img\.moegirl\.org\.cn/common(/thumb)?/./../([^\"|/ \n]+)", text)
    result = []
    for link in links:
        link = link[1]
        if "." not in link:
            print(link, text)
        else:
            result.append(link)
    return [urllib.parse.unquote(link, encoding='utf-8', errors="replace").strip() for link in result]


@deprecated
def parse_gallery(text: str) -> List[str]:
    parsed = wtp.parse(text)
    result = []
    for tag in parsed.get_tags("gallery"):
        content = tag.contents.strip()
        lines = [line for line in content.split("\n") if not is_empty(line)]
        for line in lines:
            args = line.split("|")
            for arg in args:
                if "." in arg and len(arg.split(".")[-1]):
                    pass
    return result


def search_pages(*search_strings, preload: bool = True) -> Iterable[Page]:
    """
    搜索主名字空间下，源代码有任意关键词的条目
    :param search_strings: 关键词列表
    :param preload: 是否预先批量加载列表中的页面
    :return: Page对象
    """
    from utils.sites import mgp
    gen = GeneratorFactory(site=mgp())
    gen.handle_arg('-ns:0')
    for s in search_strings:
        gen.handle_arg(f'-search:insource:"{s}"')
    gen = gen.getCombinedGenerator(preload=False)
    if preload:
        gen = PreloadingGenerator(gen, groupsize=get_rate_limit())
    return gen


CST: timezone = timezone(offset=timedelta(hours=8))


def parse_time(timestamp: str, cst: bool = False) -> datetime:
    parsed = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%SZ')\
        .replace(tzinfo=timezone.utc)
    if cst:
        parsed = parsed.astimezone(CST)
    return parsed
