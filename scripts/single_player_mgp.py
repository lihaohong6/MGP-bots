from pywikibot import Page

import init_script
from utils.sites import mgp


def main():
    contributions_page = Page(source=mgp(), title="User:Lihaohong/创建的条目")
    pages = list(contributions_page.linkedPages())
    for page in pages:
        for revision in page.revisions():
            if revision['user'] != 'Lihaohong':
                break
        else:
            print(page.title())


if __name__ == "__main__":
    main()
