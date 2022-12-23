from typing import Iterator, Dict, List

from pywikibot import Page
from pywikibot.pagegenerators import GeneratorFactory

from utils.sites import mgp

site = mgp()
target_page = Page(source=site, title="User:Lihaohong/链入消歧义页面的条目")


def get_disambig_pages():
    gen = GeneratorFactory(site=site)
    gen.handle_args(['-ns:0', '-cat:消歧义页'])
    return gen.getCombinedGenerator(preload=False)


def create_wiki_table(disambig_pages):
    result = ['{| class="wikitable"',
              "|+",
              "! 消歧义页面 !! 链入消歧义页面的条目"]
    for page in disambig_pages:
        links = set(list(p.title() for p in page.linkedPages()))
        redirects = list(page.redirects(namespaces=0))
        linked_from: Iterator[Page] = page.backlinks(namespaces=0, filter_redirects=False)
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
            redirect_string = '' if len(redirects) == 0 else '（' + '、'.join(p.title(as_link=True, allow_interwiki=False) for p in redirects) + '）'
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


def links_to_disambig():
    disambig_pages = list(get_disambig_pages())
    print("All disambig pages fetched.")
    categories = categorize(disambig_pages)
    print("All pages categorized by initials.")
    for page_name, pages in categories.items():
        print("Processing " + page_name)
        page = Page(source=site, title=target_page.title() + "/" + page_name)
        page.text = create_wiki_table(pages)
        page.save(summary="机器人试运行", botflag=False, tags="Bot")
