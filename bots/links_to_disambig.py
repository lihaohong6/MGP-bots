import sys
from argparse import ArgumentParser
from typing import Dict, List

from pywikibot import Page, APISite
from pywikibot.data.api import PropertyGenerator
from pywikibot.pagegenerators import GeneratorFactory
from pywikibot.tools.itertools import itergroup

from utils.sites import mgp
from utils.utils import adjust_trailing_newline

site: APISite = mgp()


def get_disambig_pages():
    """
    Get all disambiguation pages in ns0.
    :return: A generator of all disambiguation pages
    """
    gen = GeneratorFactory(site=site)
    gen.handle_args(['-ns:0', '-cat:消歧义页'])
    return gen.getCombinedGenerator(preload=False)


def index_of(pages: List[Page], title: str):
    """
    Get the index of a page in a list
    :param pages: A list of Page objects
    :param title: The title of the target page
    :return: The index of the desired page
    """
    for index, page in enumerate(pages):
        if page.title() == title:
            return index
    raise RuntimeError(f"Index of {title} cannot be found because it is not in the list.")


def batch_page_links(pages):
    """
    Get all pages linked from each page in the list. This is done in batch to reduce the number of requests.
    :param pages: A list of pages.
    :return: A parallel list of the pages parameter. Each corresponding element is a list of page titles.
    """
    gen = PropertyGenerator(prop='links', site=site, pllimit=500, titles="|".join(p.title() for p in pages), plnamespace=0)
    result = [[] for _ in range(50)]
    for page in gen:
        res = []
        if 'links' in page:
            res = [link['title'] for link in page['links']]
        # results are not in order, so we need to look for the correct index here
        result[index_of(pages, page['title'])] = res
    return result


def batch_page_redirects(pages):
    """
    Get all pages that redirect to each page in the list. This is done in batch to reduce the number of requests.
    :param pages: A list of pages.
    :return: A parallel list of the pages parameter. Each corresponding element is a list of page titles.
    """
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
    """
    Sends requests to the server to build the final wikitable.
    :param disambig_pages: A list of disambiguation pages to be in the final table
    :return: A wikitable string consisting of disambiguation pages, their redirects,
    and pages that link to them.
    """
    result = ['{| class="wikitable"',
              "|+",
              "! 消歧义页面 !! 链入消歧义页面的条目"]
    curr, total = 0, len(disambig_pages)
    # process pages in batches of 50
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
                # links is the white list
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
    """
    Put a list of pages in several buckets based on the pinyin of the first character.
    :param pages: A list of pages to the processed.
    :return: A dictionary mapping the name of the bucket to the corresponding list.
    """
    import pinyin
    # this can be adjusted to any arbitrary list.
    buckets = ['A-C', 'D-F', 'G-I', 'J-L', 'M-O', 'P-R', 'S-U', 'V-X', 'Y-Z', '其它']
    # initially, each bucket is an empty list
    result = dict((b, []) for b in buckets)
    for page in pages:
        # transform the title to a single upper case letter (or a special character)
        title_transformed = pinyin.get_initial(page.title()[0])
        if title_transformed.isascii():
            title_transformed = title_transformed.upper()
        for bucket in buckets:
            # try each bucket; if the last one is reached, we have a special character
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
    args = sys.argv[2]
    parser = ArgumentParser()
    parser.add_argument("target", nargs=1, help="The target page.", type=str)
    parser.add_argument("-f", "--filter", dest="filter", type=str,
                        help="Page categories to use. Separated by commas.")
    args = parser.parse_args(args)
    target_page = args.target
    disambig_pages = list(get_disambig_pages())
    print("All disambig pages fetched.")
    categories = categorize(disambig_pages)
    print("All pages categorized by initials.")
    valid_categories = categories.keys() if args.filter is None else set(args.filter.split(","))
    for page_name, pages in categories.items():
        if page_name in valid_categories:
            print("Processing " + page_name)
        else:
            print("Skipping " + page_name)
        page = Page(source=site, title=target_page + "/" + page_name)
        page.text = adjust_trailing_newline(create_wiki_table(pages), 2) + "[[Category:萌娘百科数据报告]]"
        page.save(summary="更新列表", botflag=True, tags="Bot")


def links_to_disambig():
    run_links_to_disambig()
    # print(batch_page_links([Page(source=mgp(), title="魔剑士莉奈2"), Page(source=mgp(), title="User:Lihaohong")]))
