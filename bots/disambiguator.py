import sys
from typing import List, Any, Set, Optional, Tuple

from pywikibot import Page
from pywikibot.bot import SingleSiteBot
from pywikibot.pagegenerators import PreloadingGenerator
from wikitextparser import parse

from utils.sites import mgp, mirror
from utils.user_interact import prompt_choices
from utils.utils import generate_possible_titles

site = mgp()


def disambiguate_page_text(text: str, choices: List[str], replace: Set[str],
                           test: List[int] = None, page_link: str = None, page_title: str = None,
                           replacements: List[Tuple[str, str]] = None) -> Optional[str]:
    lines = text.split("\n")
    text_changed = False
    for index, line in enumerate(lines):
        line_changed = False
        parsed = parse(line)
        for link in parsed.wikilinks:
            if link.title in replace:
                if page_link is not None and page_title is not None:
                    print("\n" + page_title + "：" + page_link)
                print("=" * 10 + "\n" + "\n".join(lines[index - 2:index + 3]) + "\n" + "=" * 10)
                if test is None:
                    choice = prompt_choices("Which link? Input 0 to skip.",
                                            choices,
                                            allow_zero=True)
                else:
                    choice = test.pop(0)
                if choice == 0:
                    continue
                choice = choices[choice - 1]
                if link.text is None:
                    link.text = link.title
                if replacements is not None:
                    replacements.append((link.title, choice))
                link.title = choice
                line_changed = True
                text_changed = True
        if line_changed:
            lines[index] = str(parsed)
    return "\n".join(lines) if text_changed else None


class DisambiguateBot(SingleSiteBot):

    def __init__(self, replace: List[str],
                 choices: List[str],
                 limit: int = 50,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.replace = set()
        self.choices = choices
        self.limit = limit
        for title in replace:
            self.replace.update(set(generate_possible_titles(title)))

    def treat(self, page: Page) -> None:
        text = old_text = page.text
        changes = []
        text = disambiguate_page_text(text, self.choices, self.replace,
                                      page_link=page.full_url(), page_title=page.title(),
                                      replacements=changes)
        if text is None:
            return
        setattr(page, "_bot_may_edit", True)
        changes = set(changes)
        self.userPut(page=page, oldtext=old_text, newtext=text,
                     asynchronous=True, minor=True,
                     tags="Automation tool", watch="nochange",
                     summary="机器人辅助消歧义：" + "；".join(f"{c[0]}=>{c[1]}" for c in changes))
        self.limit -= 1
        if self.limit == 0:
            self.exit()


# def treat_page_list(pages, replace: List[str]):
#     gen = PreloadingGenerator(pages)
#     for page in gen:
#         text = old_text = page.text
#         setattr(page, "_text", text)


def disambiguate(page_name: str):
    page = Page(source=site, title=page_name)
    redirects = [page_name] + [p.title() for p in page.redirects(namespaces=0)]
    print("Treating " + str(redirects))
    choices = []
    for line in page.text.split("\n"):
        parsed = parse(line)
        links = parsed.wikilinks
        if len(links) == 0:
            continue
        choices.append(links[0].title)
    print("\n".join(f"{i}: {c}" for i, c in enumerate(choices)))
    backlinks = list(page.backlinks(namespaces=0))
    print(f"Treating {len(backlinks)} pages.")
    bot = DisambiguateBot(site=site,
                          generator=PreloadingGenerator(backlinks),
                          replace=redirects,
                          choices=choices)
    bot.run()


def run_disambiguator():
    args = sys.argv[2:]
    disambiguate(args[0])
