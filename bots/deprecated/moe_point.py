import webbrowser

import pywikibot
import wikitextparser as wtp
from pywikibot import Page
from pywikibot.bot import SingleSiteBot
from pywikibot.pagegenerators import GeneratorFactory
from wikitextparser import WikiLink

from utils.config import get_data_path
from utils.utils import find_templates, get_categories, get_continue_page, save_continue_page, get_page_list

SAVE_FILE_NAME = "moe_point.txt"
PAGE_LIST_NAME = "moe_point_list.txt"


def parse_moe_points(moe_points_text: wtp.WikiText):
    moe_points = moe_points_text.wikilinks
    attributes = [list() for _ in range(len(moe_points))]

    def add_attribute(target: WikiLink, attr: str):
        for index, moe_point in enumerate(moe_points):
            if moe_point.title == target.title:
                attributes[index].append(attr)
                break
        else:
            raise RuntimeError("?")

    for t in find_templates(moe_points_text.templates, "黑幕", "Heimu"):
        for link in t.wikilinks:
            add_attribute(link, "黑幕")
    for t in moe_points_text.get_tags("del"):
        for link in t.wikilinks:
            add_attribute(link, "del")
    for t in moe_points_text.get_bolds():
        for link in t.wikilinks:
            add_attribute(link, "加粗")
    return moe_points, attributes


class MoePointBot(SingleSiteBot):
    def __init__(self, generator):
        super().__init__(generator=generator)
        self.opt.always = True

    def treat(self, page: Page) -> None:
        parsed = wtp.parse(page.text)
        t = find_templates(parsed.templates, "人物信息")
        if len(t) != 1:
            pywikibot.error(f"There are {len(t)} copies of T:人物信息 in {page.title()}")
            return
        moe_points_text = t[0].get_arg("萌点")
        if moe_points_text is None:
            return
        moe_points, moe_point_attributes = parse_moe_points(moe_points_text)
        cat_links = get_categories(parsed)
        cats = dict((":".join(c.target.split(":")[1:]).strip(), c) for c in cat_links)
        # check if necessary
        if len(moe_points) == 0 or all(link.title in cats for link in moe_points):
            pywikibot.output(f"No need to process {page.title()} "
                             f"since it does not contain any uncategorized moe points")
            return
        texts = []
        for index, link in enumerate(moe_points):
            if link.text is None:
                text = link.title
            else:
                text = link.title + "," + link.text
            text += "".join("," + a for a in moe_point_attributes[index])
            texts.append(text)
        # remove redundant cats
        for text, link in cats.items():
            for moe_point in moe_points:
                # 后缀消歧义
                if moe_point.target in text or text in moe_point.target:
                    del link.string
                    break
        t[0].set_arg("萌点", "{{萌点|" + "|".join(texts) + "}}")
        # mode = input("1: use T:萌点\n2: add cats\n3: skip").strip()
        # if mode == '1':
        #     page.text = str(parsed)
        #     page.save(minor=True, summary="添加萌点分类", tags="Automation tool",
        #               confirm=False)
        # # mode2: add cats
        # elif mode == "2":
        #     pass
        # else:
        #     return
        pywikibot.output("Categories:" + str(list(cats.keys())))
        pywikibot.output("Page " + page.title())
        pywikibot.showDiff(page.text, str(parsed))
        pywikibot.output("Save? [y]es, [N]o, [e]dit, [q]uit ")
        option = input().strip().lower()
        prev = page.text
        if option == 'y':
            page.text = str(parsed)
        elif option == 'q':
            self.exit()
        elif option == 'e':
            p = get_data_path().joinpath("TEMP.txt")
            with open(p, "w") as f:
                f.write(str(parsed))
            webbrowser.open("file:" + str(p.absolute()))
            response = input("Press enter after you are done. [n]o ").lower().strip()
            if response != 'n':
                with open(p, "r") as f:
                    page.text = f.read()
        if page.text.strip() != prev.strip():
            self.userPut(page, prev, page.text, minor=True, summary="添加萌点分类", tags="Automation tool",
                         watch="nochange")
        save_continue_page(SAVE_FILE_NAME, page.title())


def moe_point_bot():
    cont = get_continue_page(SAVE_FILE_NAME)
    if cont == "!":
        cont = None
    gen = GeneratorFactory()
    gen.handle_arg("-ns:0")
    gen.handle_arg("-transcludes:T:人物信息")
    gen = get_page_list(PAGE_LIST_NAME, gen.getCombinedGenerator(preload=False), cont)
    bot = MoePointBot(generator=gen)
    bot.run()
