import pickle
import sys
from pathlib import Path

import pywikibot
import requests
from pywikibot import Page
from pywikibot.bot import SingleSiteBot
from pywikibot.pagegenerators import PreloadingGenerator
import wikitextparser as wtp

from utils.config import get_default_save_params
from utils.utils import search_pages

BOILERPLATE_BOT_SUMMARY = "去除预加载"
BOILERPLATE_PATH = Path("texts/boilerplates")
AUTO_PATH = BOILERPLATE_PATH.joinpath("auto.pickle")
if AUTO_PATH.exists():
    black_list = set(pickle.load(open(AUTO_PATH, "rb")))
else:
    print("Black list does not exist!")
    black_list = set()


def should_remove(text: str) -> bool:
    if text in black_list:
        return True
    return False


def treat_boilerplate(text: str) -> str:
    parsed = wtp.parse(text)
    for c in parsed.comments:
        if should_remove(c.contents.strip()):
            c.string = ""
    return str(parsed)


class BoilerplateBot(SingleSiteBot):
    def treat(self, page: Page) -> None:
        text = treat_boilerplate(page.text)
        if text != page.text:
            page.text = text
            page.save(summary=BOILERPLATE_BOT_SUMMARY, **get_default_save_params())


def download_boilerplate():
    from bs4 import BeautifulSoup
    import urllib

    from utils.sites import mgp

    response = requests.get("https://mzh.moegirl.org.cn/index.php?title=Special%3A%E5%89%8D%E7%BC%80%E7%B4%A2%E5%BC%95"
                            "&prefix=%E9%A1%B5%E9%9D%A2%E6%A0%BC%E5%BC%8F&namespace=10").text
    soup = BeautifulSoup(response, 'html.parser')
    pages = []
    for link in soup.find_all(name="a"):
        href = urllib.parse.unquote(link.attrs['href'], encoding='utf-8')
        if '/' == href[0]:
            href = href[1:]
        if 'Template:页面格式/' in href and '/doc' not in href:
            pages.append(Page(source=mgp, title=href))

    result = set()
    for index, page in enumerate(PreloadingGenerator(pages)):
        print(f"Processing page {index}: " + page.title())
        for revision in page.revisions(content=True):
            parsed = wtp.parse(revision['*'])
            for comment in parsed.comments:
                s = comment.contents.strip()
                if s != "":
                    result.add(s)

    BOILERPLATE_PATH.mkdir(parents=True, exist_ok=True)
    pickle.dump(result, open(AUTO_PATH, "wb"))


def run_boilerplate_bot():
    keywords = sys.argv[2:]
    bot = BoilerplateBot(generator=search_pages(*keywords, preload=True))
    bot.run()
