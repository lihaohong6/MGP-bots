import re
from typing import Iterable

import requests
from pywikibot import Page
from pywikibot.exceptions import InvalidTitleError
from pywikibot.pagegenerators import GeneratorFactory
from pywikibot.tools import itergroup

from utils.config import get_data_path
from utils.sites import cm, mgp
from utils.utils import get_commons_links, get_page_list, get_continue_page, save_continue_page

exclude = {'Logo youtube.png', 'Bilibili Logo Blue.svg', 'Bilibilitv-logo.png', 'Nijisanji_temp.png',
           'Twitter logo.svg', 'Nijisanji Logo.png', 'HololiveMusicLogo.png', 'TikTok Logo.svg',
           'Holodex Logo.svg', 'hololive.PNG', 'YouTube Logo icon.png', 'Twitch Logo.png',
           'Hololive production.png', 'Flag_of_China.svg', 'Flag_of_Japan.svg', '萌薇头像.png',
           'AcFun Logo.svg', 'AVI联盟标志.png', '虚研学园logo（透明底）.png', '虚研社去底logo.png', 'NIJISANJI.png',
           'ChaosLive图标.png'}
exclude = {Page(source=cm, title="File:" + e).title() for e in exclude}


def find_image_links(page: Page):
    expanded = page.expand_text()
    images = {p.title() for p in page.imagelinks()}
    file_paths = re.findall("{{filepath:([^}]+)}}", expanded)
    images = set.union(images,
                       set(file_paths),
                       set(get_commons_links(expanded)))
    result = set()
    for image in images:
        p = Page(source=cm,
                 title="File:" + image if not re.search("file:", image, re.IGNORECASE)
                 else image)
        try:
            result.add(p.title())
        except InvalidTitleError:
            pass
    return result.difference(exclude)


CONT_FILE = "vtuber_commons_cat_continue.txt"


def query_cats(files: Iterable[str]):
    result = []
    for sublist in itergroup(files, 50):
        url = "https://commons.moegirl.org.cn/api.php"
        response = requests.get(url, params={
            "action": 'query',
            'prop': 'categories',
            "cllimit": 500,
            'titles': "|".join(sublist),
            # 'clcategories': page.title(),
            'format': 'json'
        }).json()['query']['pages'].values()
        result.extend(response)
    return result


def vtuber_commons_cat():
    gen = GeneratorFactory()
    gen.handle_arg("-ns:0")
    gen.handle_arg("-catr:虚拟UP主")
    pages = get_page_list(file_name="vtuber_commons_cat_pages.txt",
                          factory=gen.getCombinedGenerator(preload=False),
                          cont=get_continue_page(CONT_FILE),
                          site=mgp)
    for page in pages:
        files = find_image_links(page)
        output = ""
        if len(files) == 0:
            print("No images on " + page.title())
            continue
        response = query_cats(files)
        output += "*[[" + page.title() + "]]\n"
        for result in response:
            if 'categories' in result:
                cats = {c['title'].replace('Category:', '') for c in result['categories']}
            else:
                cats = set()
            cats.discard("原作者保留权利")
            if page.title() in cats:
                continue
            output += f"**[[cm:{result['title']}|{result['title']}]]" \
                      f"（{'、'.join(cats)}）\n"
        with open(get_data_path().joinpath("vtuber_commons_cat_result.txt"), "a") as f:
            f.write(output)
        save_continue_page(CONT_FILE, page.title())
