# This is a sample Python script.

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.
import re
from pathlib import Path
from typing import List

import pywikibot
from pywikibot import Page
from pywikibot.pagegenerators import GeneratorFactory
from wikitextparser import WikiLink
import wikitextparser as wtp

import utils.login
from bots.barn_star import auto_star
from bots.commons_image import commons_image
from bots.inter_wiki import InterWikiBot
from bots.moe_point import moe_point_bot
from bots.template_adder import TemplateAdderBot
from bots.vtuber_commons_cat import vtuber_commons_cat
from bots.vtuber_infobox import VtuberInfoboxBot
from utils.config import get_data_path, lang_map
from utils.logger import setup_logger
from utils.utils import find_templates, is_empty

message_body = """{| style="background-color: #fdffe7; border: 1px solid #fceb92;"
|rowspan="2" style="vertical-align: middle; padding: 5px;" | [[File:20190123140753.png|100px]]
|style="font-size: x-large; padding: 3px 3px 0 3px; height: 1.5em;" | '''兰斯星章'''
|-
|style="vertical-align: middle; padding: 3px;" | 感谢您为萌百的[[兰斯系列]]条目做出的贡献！~~~
|}"""


def temp():
    generator = GeneratorFactory()
    generator.handle_arg("-catr:虚拟UP主")
    lst = []
    counter = 0
    out = get_data_path().joinpath("vtuber_list.txt")
    for page in generator.getCombinedGenerator(preload=True):
        parsed = wtp.parse(page.text)
        t = find_templates(parsed.templates, "infobox", "信息栏", loose=True)
        if len(t) == 1:
            region = t[0].get_arg("出身地区")
            if region is not None and not is_empty(region.value):
                lst.append("#" + page.title(as_link=True) + ": <nowiki>" + region.value.strip() + "</nowiki>")
        counter += 1
        print(counter)
        with open(out, "w") as f:
            f.write("\n".join(lst))
    with open(out, "w") as f:
        f.write("\n".join(lst))


def vocaloid_producer_templates():
    gen = GeneratorFactory()
    gen.handle_arg("-cat:虚拟歌手音乐人模板")
    gen = gen.getCombinedGenerator(preload=True)
    for p in gen:
        if p.title(with_ns=False) == "Creuzer":
            break
    for p in gen:
        bot = TemplateAdderBot(p.title(with_ns=False))
        bot.run()


def main():
    setup_logger()
    get_data_path().mkdir(exist_ok=True)
    # commons_image()
    vtuber_commons_cat()


if __name__ == '__main__':
    main()
