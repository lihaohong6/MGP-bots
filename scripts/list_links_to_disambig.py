from typing import Iterator

from init_script import init
from pywikibot import Site, Page

from pywikibot.pagegenerators import GeneratorFactory, PreloadingGenerator

init()

site = Site(fam="mirror")


def get_disambig_pages():
    gen = GeneratorFactory(site=site)
    gen.handle_args(['-ns:0', '-cat:消歧义页'])
    return gen.getCombinedGenerator(preload=False)


def main():
    disambig_pages = PreloadingGenerator(get_disambig_pages(), groupsize=500)
    file = open("output.txt", "w")
    file.write('{| class="wikitable"\n')
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
            file.write("|-\n")
            file.write(f"| {page.title(as_link=True)} "
                       f"{'' if len(redirects) == 0 else '（' + '、'.join(p.title(as_link=True) for p in redirects) + '）'} || " +
                       "、".join(p.title(as_link=True) for p in problematic_pages) +
                       "\n")
            file.flush()
    file.close()


if __name__ == '__main__':
    main()
