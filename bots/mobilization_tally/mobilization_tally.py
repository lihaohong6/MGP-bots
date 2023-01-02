import sys
from argparse import ArgumentParser
from datetime import datetime, timedelta
from typing import Dict, Callable, List

import wikitextparser as wtp
from pywikibot import APISite, Page, User
from wikitextparser import Section

from bots.mobilization_tally.presets import Preset, get_preset
from bots.mobilization_tally.update_scoreboard import parse_section_title_username, USERNAME_SECTION_LEVEL, \
    SCORE_SECTION_LEVEL, update_scoreboard
from bots.mobilization_tally.utils import username_to_section_title, set_site, get_site
from utils.sites import get_site_by_name
from utils.utils import adjust_trailing_newline


def add_results(results: List[str], section: Section):
    links = set(link.title for link in section.wikilinks)
    section.contents = adjust_trailing_newline(section.contents, 1)
    for result in results:
        parsed = wtp.parse(result)
        title = parsed.wikilinks[0].title
        if title in links:
            continue
        links.add(title)
        section.contents += "#" + result + "\n"


def apply_preset(preset: Preset, contributions: list, parsed: Section):
    for preset_name, preset_function in preset.items():
        results = []
        for c in contributions:
            line = preset_function(c)
            if line is not None:
                results.append(line)
        if len(results) == 0:
            continue
        for section in parsed.sections:
            if section.level == SCORE_SECTION_LEVEL and section.title.strip() == preset_name:
                target_section = section
                break
        else:
            equal = SCORE_SECTION_LEVEL * "="
            parsed.string = adjust_trailing_newline(parsed.string) + \
                            f"{equal} {preset_name} {equal}\n"
            target_section = parsed.sections[-1]
        add_results(results, target_section)


def get_mobilization_participants(target: str):
    signup_page = Page(source=get_site(), title=target + "/报名")
    parsed = wtp.parse(signup_page.text)
    section = parsed.sections[1]
    return [User(source=get_site(), title=link.title)
            for link in section.wikilinks
            if link.title[0] == 'U']


def list_contributions(target: str, preset: str, **kwargs):
    # get list of participants
    users = get_mobilization_participants(target)
    print("Participants: " + ", ".join(u.username for u in users))
    site = get_site()
    contributions_page = Page(source=site, title=target + "/计分板")
    parsed = wtp.parse(contributions_page.text)
    preset = get_preset(preset)
    for user in users:
        contributions = [
            {
                'page': Page(source=site, title=c['title']),
                'ns': c['ns'],
                'timestamp': datetime.strptime(c['timestamp'], '%Y-%m-%dT%H:%M:%SZ'),
                'new': 'new' in c,
                'comment': c['comment']
            }
            for c in site.usercontribs(user=user, total=500)]
        contributions = [c for c in contributions if c['timestamp'] > datetime.now() + timedelta(hours=-50)]
        for section in parsed.sections:
            if section.level == USERNAME_SECTION_LEVEL and \
                    parse_section_title_username(section.title.strip()) == user.username:
                target_section = section
                break
        else:
            equals = USERNAME_SECTION_LEVEL * "="
            parsed.string = adjust_trailing_newline(parsed.string) + \
                            f"{equals} {username_to_section_title(user.username)} {equals}\n"
            target_section = parsed.sections[-1]
        apply_preset(preset, contributions, target_section)
    contributions_page.text = str(parsed)
    contributions_page.save(summary="更新计分板（试运行）", minor=True)


def run_mobilization_tally():
    parser = ArgumentParser()
    parser.add_argument("command", nargs=1)
    parser.add_argument("target", nargs=1)
    parser.add_argument("-s", "--site", type=str, dest="site", default="mgp")
    parser.add_argument("-p", "--preset", type=str, dest="preset", default="vj")
    args = parser.parse_args(sys.argv[2:])
    set_site(get_site_by_name(args.site))
    dispatcher: Dict[str, Callable[..., None]] = {
        'scoreboard': update_scoreboard,
        'list_contributions': list_contributions
    }
    command = args.command[0]
    if command in dispatcher:
        dispatcher[command](target=args.target[0], preset=args.preset)
    else:
        print(", ".join(dispatcher.keys()))
