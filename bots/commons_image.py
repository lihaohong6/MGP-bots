import pickle
from re import findall
from time import sleep
from typing import List, Dict, Set, Tuple, Iterable

import pywikibot as pwb
import requests
import wikitextparser as wtp
from pywikibot import pagegenerators, Page
from pywikibot.exceptions import InvalidTitleError
from pywikibot.pagegenerators import GeneratorFactory

from utils.config import get_data_path
from utils.sites import cm, mgp
from utils.utils import get_page_list, get_continue_page, save_continue_page, adjust_trailing_newline


def deprecated():
    site = pwb.Site(fam="commons")
    gen = site.querypage("GloballyUnusedFiles", total=None)
    gen = pagegenerators.PreloadingGenerator(gen)
    for page in gen:
        if not page.exists():
            continue
        print("Working on " + page.title())
        url = "https://mzh.moegirl.org.cn/api.php"
        response = requests.get(url, params={
            "action": "query",
            "list": "search",
            "srsearch": 'insource:"{}"'.format(page.title(with_ns=False)),
            "srnamespace": "*",
            "format": "json"
        })
        if response.json()['query']['searchinfo']['totalhits'] > 0:
            need_template = True
            if page.text is not None:
                parsed = wtp.parse(page.text)
                for t in parsed.templates:
                    if t.name.strip() == "非链入使用":
                        print(page.title() + " already contains template")
                        need_template = False
                        break
            if need_template:
                print(page.title() + " needs T:非链入使用")
        sleep(3)


MGP_CONTINUE_FILE_NAME = "commons_image_continue.txt"
COMMONS_CONTINUE_FILE_NAME = "commons_image_file_continue.txt"
TEMP_PROGRESS_FILE = get_data_path().joinpath("commons_image_temp_progress.pickle")


def load_progress() -> Dict[str, Set[str]]:
    if TEMP_PROGRESS_FILE.exists():
        return pickle.load(open(TEMP_PROGRESS_FILE, "rb"))
    return {}


def process_page(page: Page):
    files: List[str] = findall("{{filepath:([^}]+)}}", page.text)
    progress: Dict[str, Set[str]] = load_progress()
    for file in files:
        file_name = file
        s = progress.get(file_name, set())
        s.add(page.title())
        progress[file_name] = s
    pickle.dump(progress, open(TEMP_PROGRESS_FILE, "wb"))
    save_continue_page(MGP_CONTINUE_FILE_NAME, page.title())


def get_files_global_usage(files: List[Page]) -> List[Page]:
    file_names = dict((f.title(), f) for f in files)
    url = "https://commons.moegirl.org.cn/api.php"
    response = requests.get(url, params={
        'action': 'query',
        'prop': 'globalusage',
        'titles': "|".join(f.title() for f in files),
        'format': 'json',
        'guprop': 'namespace',
    }).json()
    pages = response['query']['pages']
    result = []
    for key in pages:
        value = pages[key]
        usages = value['globalusage']
        if len(usages) >= 10:
            continue
        if len(usages) == 0 or all(usage['ns'] == '2' for usage in usages):
            result.append(file_names[value['title']])
    return result


def page_links(pages: Iterable[str]):
    pages = list(pages)
    too_long = False
    if len(pages) > 10:
        too_long = True
        pages = pages[:10]
    names = "、".join("[[zhmoe:" + p + "]]" for p in pages)
    if too_long:
        names += "等"
    return names


def process_batch(pages: List[Tuple[Page, Set[str]]]):
    page_names = dict((page[0].title(), page) for page in pages)
    pages = get_files_global_usage([p[0] for p in pages])
    for p in pages:
        page, references = p, page_names[p.title()][1]
        if "非链入使用" in page.text:
            raise RuntimeError()
        page.text = adjust_trailing_newline(page.text, 1) + "{{非链入使用|" + page_links(references) + "}}"
        page.save(summary="添加[[T:非链入使用]]", watch="nochange", tags="Bot", minor=True)
        save_continue_page(COMMONS_CONTINUE_FILE_NAME, page.title())


def filter_page_names(names) -> Tuple[List[str], List[str]]:
    result = []
    problematic = []
    for name in names:
        p = Page(source=cm, title="File:" + name)
        try:
            t = p.title()
            result.append(name)
        except InvalidTitleError:
            problematic.append(name)
    return result, problematic


def commons_image():
    gen = GeneratorFactory(site=mgp)
    gen.handle_arg('-search:insource:"filepath"')
    # gen.handle_arg('-search:insource:"img.moegirl"')
    pages = get_page_list("commons_image_page_list.txt",
                          gen.getCombinedGenerator(preload=False),
                          get_continue_page(MGP_CONTINUE_FILE_NAME))
    for page in pages:
        process_page(page)
    progress = load_progress()
    page_names, problematic_pages = filter_page_names(progress.keys())
    mgp_pages = set()
    for p in problematic_pages:
        for name in progress[p]:
            mgp_pages.add(name)
    print(mgp_pages)
    pages = []
    for s in page_names:
        p = Page(source=cm, title="File:" + s)
        pages.append(p)
        progress[p.title()] = progress[s]
    pages = get_page_list("commons_image_file_list.txt",
                          pages,
                          cont=get_continue_page(COMMONS_CONTINUE_FILE_NAME),
                          site=cm)
    queue = []
    for page in pages:
        if "非链入使用" not in page.text:
            queue.append((page, progress[page.title()]))
        if len(queue) == 50:
            process_batch(queue)
            queue = []
    if len(queue) > 0:
        process_batch(queue)
