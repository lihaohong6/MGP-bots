import pickle
from pathlib import Path
from typing import Any

import requests
from pywikibot import Page, APISite
from pywikibot.bot import SingleSiteBot
from pywikibot.pagegenerators import GeneratorFactory, PreloadingGenerator

from utils.config import get_default_save_params


def treat_boilerplate(text: str) -> str:
    pass


BOILERPLATE_BOT_SUMMARY = "去除预加载"


class BoilerplateBot(SingleSiteBot):
    def treat(self, page: Page) -> None:
        text = treat_boilerplate(page.text)
        if text != page.text:
            page.text = text
            page.save(summary=BOILERPLATE_BOT_SUMMARY, **get_default_save_params())


def download_boilerplate():
    from bs4 import BeautifulSoup
    import urllib
    import wikitextparser as wtp

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

    result = []
    for page in PreloadingGenerator(pages):
        parsed = wtp.parse(page.text)
        for comment in parsed.comments:
            s = comment.contents.strip()
            if s != "":
                result.append(s)

    path = Path("texts/boilerplates")
    path.mkdir(parents=True, exist_ok=True)
    file_path = path.joinpath("auto.txt")
    pickle.dump(result, open(file_path, "wb"))
