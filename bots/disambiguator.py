import re
import sys
from typing import List, Any, Set, Optional, Tuple

from pywikibot import Page
from pywikibot.bot import SingleSiteBot
from pywikibot.pagegenerators import PreloadingGenerator
from wikitextparser import parse, WikiLink

from utils.sites import mgp, mirror
from utils.user_interact import prompt_choices
from utils.utils import generate_possible_titles, find_templates, change_internal_link

site = mgp()


def disambiguate_page_text(text: str, choices: List[str], replace: Set[str],
                           test: List[int] = None, page_link: str = None, page_title: str = None,
                           replacements: List[Tuple[str, str]] = None) -> Optional[str]:
    if replacements is None:
        replacements = []
    text_changed = False

    def get_choice(message):
        if page_link is not None and page_title is not None:
            print("\n" + page_title + "：" + page_link)
        print(message)
        if test is None:
            choice = prompt_choices("Which link? Input 0 to skip.",
                                    choices,
                                    allow_zero=True)
        else:
            choice = test.pop(0)
        return choice

    def change_title(link: WikiLink, title: str):
        if link.text is None:
            link.text = link.title
        change_internal_link(link, new_title=title)

    def disambiguate_templates():
        nonlocal text_changed
        parsed = parse(text)
        templates = find_templates(parsed.templates, "VOCALOID_Chinese_Ranking/bricks",
                                   "VOCALOID_&_UTAU_Ranking/bricks")
        changed = False
        for t in templates:
            song_name = t.get_arg("曲名")
            if song_name is None:
                continue
            song_name = song_name.value.strip()
            if song_name not in replace:
                continue
            message = t.get_arg("时间")
            message = "" if message is None else message.value.strip()
            choice = get_choice(message)
            if choice == 0:
                continue
            choice = choices[choice - 1]
            if song_name in choice and song_name == choice[0:len(song_name)]:
                t.set_arg("后缀 ", choice[len(song_name):], after="曲名")
            else:
                t.set_arg("条目 ", choice, after="曲名")
            changed = True
            text_changed = True
            replacements.append((song_name, choice))
        return str(parsed) if changed else text

    def disambiguate_plain_links():
        nonlocal text_changed
        lines = text.split("\n")
        for index, line in enumerate(lines):
            line_changed = False
            parsed = parse(line)
            for link in parsed.wikilinks:
                if link.title in replace:
                    choice = get_choice("=" * 10 + "\n" + "\n".join(lines[index - 2:index + 3]) + "\n" + "=" * 10)
                    if choice == 0:
                        continue
                    choice = choices[choice - 1]
                    replacements.append((link.title, choice))
                    change_title(link, choice)
                    line_changed = True
                    text_changed = True
            if line_changed:
                lines[index] = str(parsed)
        return "\n".join(lines)

    text = disambiguate_plain_links()
    text = disambiguate_templates()

    return text if text_changed else None


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


def filter_choices(choices: List[str]) -> List[str]:
    gen = PreloadingGenerator(generator=(Page(source=site, title=c) for c in choices))
    result = []
    for p in gen:
        if p.exists() and p.text[0] == '#':
            p = p.getRedirectTarget() if p.isRedirectPage() else p
        result.append(p.title())
    return result


def get_disambiguation_choices(text: str) -> List[str]:
    choices = []
    for line in text.split("\n"):
        if "——" in line:
            parts = re.split(r"]].*—+", line)
            if len(parts) < 2:
                continue
            line = parts[0] + "]]"
        parsed = parse(line)
        links = parsed.wikilinks
        if len(links) == 0:
            continue
        # if Page(source=site, title=links[0].title).namespace().id != 0:
        #     continue
        choices.append(links[0].title.strip())
    choices = filter_choices(choices)
    return choices


def disambiguate(page_name: str):
    page = Page(source=site, title=page_name)
    redirects = [page_name] + [p.title() for p in page.redirects(namespaces=0)]
    print("Treating " + str(redirects))
    choices = get_disambiguation_choices(page.text)
    print("\n".join(f"{i + 1}: {c}" for i, c in enumerate(choices)))
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
