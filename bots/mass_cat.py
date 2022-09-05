import re
import sys
import webbrowser
from argparse import ArgumentParser
from pathlib import Path
from typing import Optional, List, Set

import pywikibot
from pywikibot import Page

from utils.config import get_data_path
from utils.sites import mgp, cm
from utils.utils import get_categories

import wikitextparser as wtp


def process_page_text(old_text: str, cat_remove: Set[str], cat_add: Page):
    parsed = wtp.parse(old_text)
    cats = get_categories(parsed)
    for cat in cats:
        cat_name = ":".join(cat.title.split(":")[1:])
        if cat_name in cat_remove:
            cat.string = ""
    return str(parsed).rstrip() + "\n" + "[[" + cat_add.title(with_ns=True) + "]]"


def adjust_blacklist(line: str, category_blacklist: Set):
    while True:
        try:
            cats = re.search(r"]]（([^）]*)）", line).group(1).split("、")
            candidates = [c for c in cats if c not in category_blacklist]
            if len(candidates) == 0:
                print("All cats in black list. ")
                return
            print("\n".join(str(index) + ":" + c for index, c in enumerate(candidates)))
            response = input("Use comma or space to separate multiple cats.")
            choices = map(int, re.split("[, ，　]+", response))
            for c in choices:
                category_blacklist.add(candidates[c])
            break
        except Exception as e:
            print(e)


def mass_cat():
    parser = ArgumentParser()
    parser.add_argument("-f", "--file", dest="file", type=Path, default=get_data_path().joinpath("in.txt"))
    args = parser.parse_args(sys.argv[2:])
    file_path: Path = args.file
    print(str(file_path.absolute()))
    curr_page: Optional[Page] = None
    curr_cat: Optional[Page] = None
    skip_page = False
    no_confirm = False
    category_blacklist = set()
    for line in open(file_path, 'r', encoding='utf-8').read().splitlines():
        if line[0:2] == '**':
            file_name = re.search(r"\[\[cm:File:([^|]+)\|", line).group(1)
            file_page = Page(source=cm, title="File:" + file_name)
            if skip_page:
                continue
            while True:
                print("Add " + curr_cat.title() + " to " + file_name + "?")
                new_text = process_page_text(file_page.text, category_blacklist, curr_cat)
                if no_confirm:
                    response = 'y'
                else:
                    pywikibot.showDiff(file_page.text, new_text)
                    response = input("[y]es; [n]o; [r]emove category; "
                                     "[a]ll files on page; [o]pen in browser: ")
                if len(response) == 1:
                    if response == 'y':
                        file_page.text = new_text
                        file_page.save(summary="添加分类", watch="nochange", minor=True, tags="Bot")
                        break
                    elif response == 'n':
                        break
                    elif response == 'r':
                        adjust_blacklist(line, category_blacklist)
                        continue
                    elif response == 'a':
                        no_confirm = True
                        break
                    elif response == 'o':
                        webbrowser.open(file_page.full_url())
                        continue
        elif line[0:1] == '*':
            no_confirm = False
            skip_page = False
            category_blacklist = set()
            page_name = re.search(r"\[\[([^]]+)]", line).group(1)
            curr_page = Page(source=mgp, title=page_name)
            curr_cat = Page(source=cm, title="Cat:" + page_name)
            while True:
                print("Processing " + curr_page.title())
                response = input("[y]es continue; [n]o, skip page; [r]eplace cat name; [o]pen cat in browser: ")
                if len(response) == 1:
                    if response == 'y':
                        break
                    if response == 'n':
                        skip_page = True
                        break
                    if response == 'r':
                        cat_name = input("Name? ")
                        curr_cat = Page(source=cm, title="Cat:" + cat_name)
                        break
                    if response == 'b':
                        webbrowser.open(curr_cat.full_url())
                        continue
            if not skip_page and not curr_cat.exists():
                while True:
                    response = input("Create cat? [y]es; [n]o")
                    if len(response) == 1:
                        if response == 'y':
                            curr_cat.text = "{{虚拟角色/虚拟UP主}}"
                            curr_cat.save(summary="新分类")
                        elif response != 'n':
                            continue
                        break

