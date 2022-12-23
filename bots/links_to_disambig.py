from typing import Iterator, Dict, List

from pywikibot import Page, APISite
from pywikibot.data.api import QueryGenerator, APIGenerator, Request, PropertyGenerator, ListGenerator
from pywikibot.pagegenerators import GeneratorFactory
from pywikibot.tools.itertools import itergroup

from utils.sites import mgp, mirror

site: APISite = mgp()
target_page = Page(source=site, title="User:Lihaohong/链入消歧义页面的条目")


def get_disambig_pages():
    gen = GeneratorFactory(site=site)
    gen.handle_args(['-ns:0', '-cat:消歧义页'])
    return gen.getCombinedGenerator(preload=False)


def index_of(pages: List[Page], title: str):
    for index, page in enumerate(pages):
        if page.title() == title:
            return index
    raise RuntimeError()


def batch_page_links(pages):
    gen = PropertyGenerator(prop='links', site=site, pllimit=500, titles="|".join(p.title() for p in pages), plnamespace=0)
    result = [[] for _ in range(50)]
    for page in gen:
        res = []
        if 'links' in page:
            res = [link['title'] for link in page['links']]
        result[index_of(pages, page['title'])] = res
    return result


def batch_page_redirects(pages):
    gen = PropertyGenerator(prop='redirects', site=site, rdlimit=500, titles="|".join(p.title() for p in pages),
                            rdnamespace=0)
    result = [[] for _ in range(50)]
    for page in gen:
        res = []
        if 'redirects' in page:
            res = [Page(source=site, title=link['title']) for link in page['redirects']]
        result[index_of(pages, page['title'])] = res
    return result


def create_wiki_table(disambig_pages):
    result = ['{| class="wikitable"',
              "|+",
              "! 消歧义页面 !! 链入消歧义页面的条目"]
    curr, total = 0, len(disambig_pages)
    for page_batch in itergroup(disambig_pages, size=50):
        links_batch = batch_page_links(page_batch)
        redirects_batch = batch_page_redirects(page_batch)
        for index, page in enumerate(page_batch):
            curr += 1
            print(f"{curr}/{total}")
            links = set(links_batch[index])
            redirects = redirects_batch[index]
            linked_from = page.backlinks(filter_redirects=False, namespaces=0)
            problematic_pages = []
            fine_pages = []
            for p in linked_from:
                if p.title() not in links:
                    problematic_pages.append(p)
                else:
                    fine_pages.append(p)
            if len(problematic_pages) > 0:
                result.append("|-")
                # list redirects in parentheses (if there are any)
                redirect_string = '' if len(redirects) == 0 else '（' + '、'.join(
                    p.title(as_link=True, allow_interwiki=False) for p in redirects) + '）'
                result.append(f"| {page.title(as_link=True, allow_interwiki=False)}{redirect_string} ||" +
                              # list problematic pages
                              "、".join(p.title(as_link=True, allow_interwiki=False) for p in problematic_pages))
    result.append('|}')
    return "\n".join(result)


def categorize(pages: List[Page]) -> Dict[str, List[Page]]:
    import pinyin
    buckets = ['A-C', 'D-F', 'G-I', 'J-L', 'M-O', 'P-R', 'S-U', 'V-X', 'Y-Z', '其它']
    result = dict((b, []) for b in buckets)
    for page in pages:
        title_transformed = pinyin.get_initial(page.title()[0])
        if title_transformed.isascii():
            title_transformed = title_transformed.upper()
        for bucket in buckets:
            # try each bucket; if the last one is reached,
            if '-' in bucket:
                start, end = bucket.split('-')
                if start <= title_transformed <= end:
                    result[bucket].append(page)
                    break
            else:
                result[bucket].append(page)
    return result


def run_links_to_disambig():
    site.login()
    disambig_pages = list(get_disambig_pages())
    print("All disambig pages fetched.")
    categories = categorize(disambig_pages)
    print("All pages categorized by initials.")
    for page_name, pages in categories.items():
        print("Processing " + page_name)
        page = Page(source=site, title=target_page.title() + "/" + page_name)
        page.text = create_wiki_table(pages)
        page.save(summary="机器人试运行", botflag=True, tags="Bot")


def links_to_disambig():
    run_links_to_disambig()
    # print(batch_page_links([Page(source=mgp(), title="魔剑士莉奈2"), Page(source=mgp(), title="User:Lihaohong")]))
