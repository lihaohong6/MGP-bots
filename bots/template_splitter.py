import re
import sys
from argparse import ArgumentParser
from typing import Dict, List, Set

import wikitextparser as wtp
from pywikibot import Page
from pywikibot.pagegenerators import PreloadingGenerator

from utils.config import get_default_save_params
from utils.sites import mgp, get_site_by_name
from utils.utils import find_templates

site = mgp()


def template_splitter(name, aliases, limit: int = 50):
    template_page = Page(source=site, title="Template:" + name)
    template_names = set(p.title(with_ns=False, allow_interwiki=False)
                         for p in template_page.redirects(namespaces="Template"))
    template_names.add(name)
    template_names.update(set(aliases))
    parsed = wtp.parse(template_page.text)
    nav_boxes = [t for t in parsed.templates
                 if t.name.lower() == 'navbox' and
                 t.get_arg("1") is not None and
                 t.get_arg("1").value.strip() == 'child']
    pages_dict: Dict[str, Page] = dict()
    changed_pages = set()
    for nav in nav_boxes:
        nav_section_name = re.search(r"{#switch:([^|]+)\|", str(nav))
        if nav_section_name is None:
            print("A navbox called " + nav.name + " has no name.")
            continue
        nav_section_name = nav_section_name.group(1)
        print("Processing " + nav_section_name)
        nav_pages = [Page(source=site, title=link.title)
                     for link in nav.wikilinks]
        gen = PreloadingGenerator(nav_pages)
        process_navbox_pages(changed_pages, gen, nav_section_name, pages_dict, template_names)
    save_changed_pages(changed_pages, limit, pages_dict)


def save_changed_pages(changed_pages, limit, pages_dict):
    counter = 0
    for page_title, page in pages_dict.items():
        if limit != -1 and counter >= limit:
            print("Edit limit reached. Aborting...")
            break
        if page_title in changed_pages:
            page.save(summary="批量添加大家族模板参数", force=True, **get_default_save_params())
            counter += 1


def process_navbox_pages(changed_pages: Set[str], gen, nav_section_name: str, pages_dict: Dict[str, Page],
                         template_names: Set[str]):
    for page in gen:
        # ignore pages that don't exist
        if not page.exists():
            continue
        if '#' == page.text[0] and page.isRedirectPage():
            page = page.getRedirectTarget()
        page_title = page.title(allow_interwiki=False)
        if page_title in pages_dict:
            page = pages_dict[page_title]
        else:
            pages_dict[page_title] = page
        parsed = wtp.parse(page.text)
        target_template = find_templates(parsed.templates, *template_names)
        if len(target_template) != 1:
            print("Page " + page.title() +
                  " has no template with the desired name."
                  if len(target_template) == 0
                  else " has multiple templates with the desired name.")
            continue
        target_template = target_template[0]
        for arg in target_template.arguments:
            if arg.positional and arg.value == nav_section_name:
                break
        else:
            target_template.set_arg("", nav_section_name, positional=True)
            setattr(page, "_text", str(parsed))
            changed_pages.add(page_title)


def run_template_splitter():
    parser = ArgumentParser()
    parser.add_argument("template_names", nargs="+")
    parser.add_argument("-l", "--limit", dest="limit", type=int, default=50)
    parser.add_argument("-s", "--site", dest="site", type=str, default="mgp")
    args = parser.parse_args(sys.argv[2:])
    limit = args.limit
    if limit < 0:
        limit = -1
    global site
    site = get_site_by_name(args.site)
    template_splitter(args.template_names[0], args.template_names[1:], limit)
