import pickle
import re
import sys
from argparse import ArgumentParser
from pathlib import Path
from typing import Optional, List, Iterable

import pywikibot
import requests
from pywikibot import Page
from pywikibot.bot import SingleSiteBot
from pywikibot.pagegenerators import PreloadingGenerator
import wikitextparser as wtp

from utils.config import get_default_save_params
from utils.utils import search_pages

BOILERPLATE_BOT_SUMMARY = "去除预加载残留"
BOILERPLATE_PATH = Path("texts/boilerplates")
AUTO_PATH = BOILERPLATE_PATH.joinpath("auto.pickle")
if AUTO_PATH.exists():
    black_list = set(pickle.load(open(AUTO_PATH, "rb")))
else:
    black_list = set()


def should_remove(text: str) -> bool:
    """
    Determine whether a comment should be removed.
    Used to be complicated, but greatly simplified now.
    :param text: Comment
    :return: True if comment should be removed; false otherwise
    """
    if "保留这里的注释" in text:
        return False
    if text in {']]'}:
        return False
    if text in black_list:
        return True
    return False


def treat_boilerplate(text: str) -> str:
    # requested by LUO1P
    if '虚拟UP主' in text:
        return text
    parsed = wtp.parse(text)
    for c in parsed.comments:
        if should_remove(c.contents.strip()):
            c.string = ""
    return str(parsed)


def find_search_string(text: str) -> Optional[str]:
    chs = r'\u4E00-\u9FFF\u3400-\u4DBF'
    candidates = re.findall(rf"[{chs}a-zA-Z\d]+", text)
    candidates.sort(key=len, reverse=True)
    candidates = [c for c in candidates if re.search(f'[{chs}]', c)]
    if len(candidates) > 0 and len(candidates[0]) > 3:
        return candidates[0]
    return None


def get_search_strings() -> Iterable[str]:
    res = set()
    for w in black_list:
        r = find_search_string(w)
        if r:
            res.add(r)
    return res


class BoilerplateBot(SingleSiteBot):
    def treat(self, page: Page) -> None:
        text = treat_boilerplate(page.text)
        if text != page.text:
            page.text = text
            page.save(summary=BOILERPLATE_BOT_SUMMARY, **get_default_save_params())


def download_boilerplate():
    """
    Download boilerplate templates from subpages of Template:页面格式 (including past versions),
    extract all comments in these templates and store them in a file.
    :return: None
    """
    from bs4 import BeautifulSoup
    import urllib

    from utils.sites import mgp

    # Don't know the api for subpages, so simply parse all the links in the HTML response
    response = requests.get("https://mzh.moegirl.org.cn/index.php?title=Special%3A%E5%89%8D%E7%BC%80%E7%B4%A2%E5%BC%95"
                            "&prefix=%E9%A1%B5%E9%9D%A2%E6%A0%BC%E5%BC%8F&namespace=10").text
    soup = BeautifulSoup(response, 'html.parser')
    pages = []
    for link in soup.find_all(name="a"):
        href = urllib.parse.unquote(link.attrs['href'], encoding='utf-8')
        if '/' == href[0]:
            href = href[1:]
        if 'Template:页面格式/' in href and '/doc' not in href:
            pages.append(Page(source=mgp(), title=href))

    # find all revision of all pages and add all comments into black list
    result = set()
    for index, page in enumerate(PreloadingGenerator(pages)):
        print(f"Processing page {index}: " + page.title())
        for revision in page.revisions(content=True):
            try:
                parsed = wtp.parse(revision['*'])
                for comment in parsed.comments:
                    s = comment.contents.strip()
                    if s != "":
                        result.add(s)
            except AttributeError:
                print("Skipping a revision for page titled", page.title())

    # store black list in a file
    BOILERPLATE_PATH.mkdir(parents=True, exist_ok=True)
    pickle.dump(result, open(AUTO_PATH, "wb"))


def run_boilerplate_bot():
    # all arguments are treated as search keywords
    p = ArgumentParser()
    p.add_argument("keywords", nargs="*", default=[])
    p.add_argument("-u", "--update", action="store_true")
    p.add_argument("-a", "--all", action="store_true")
    args = p.parse_args(sys.argv[2:])
    keywords = args.keywords
    if args.update:
        pywikibot.output("Updating boilerplate templates...")
        download_boilerplate()
    if args.all:
        pywikibot.output("Using the following as search keyword: ")
        keywords = get_search_strings()
        pywikibot.output(str(keywords))
    if len(keywords) == 0:
        pywikibot.output("No search keyword provided.")
        return
    if len(black_list) == 0:
        pywikibot.warning("Black list does not exist! Please download first.")
    bot = BoilerplateBot(generator=search_pages(*keywords, preload=True))
    bot.run()
