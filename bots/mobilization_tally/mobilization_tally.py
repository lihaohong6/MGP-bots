import pickle
import sys
from argparse import ArgumentParser
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Callable, List, Union, Optional

import pywikibot
import wikitextparser as wtp
from pywikibot import Page, User
from wikitextparser import Section, WikiText

from bots.mobilization_tally.presets import Preset, get_preset, get_preset_names
from bots.mobilization_tally.update_scoreboard import parse_section_title_username, USERNAME_SECTION_LEVEL, \
    SCORE_SECTION_LEVEL, update_scoreboard
from bots.mobilization_tally.utils import username_to_section_title, set_site, get_site
from utils.config import get_data_path
from utils.sites import get_site_by_name
from utils.utils import adjust_trailing_newline, parse_time, CST


def add_results(results: List[str], section: Section):
    existing_lines = {line.strip().lstrip('*#') for line in str(section).split("\n")}
    section.contents = adjust_trailing_newline(section.contents, 1)
    for result in results:
        if result in existing_lines:
            pywikibot.info("Skipping " + result)
            continue
        existing_lines.add(result)
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


USER_CONTRIBUTION_UPDATE_FILE: Path


def get_today() -> datetime:
    now = datetime.now(tz=CST)
    return datetime(year=now.year, month=now.month, day=now.day)


def get_last_update(usernames: List[str], event_start: Optional[datetime]) -> Dict[str, datetime]:
    if USER_CONTRIBUTION_UPDATE_FILE.exists():
        result = pickle.load(open(USER_CONTRIBUTION_UPDATE_FILE, "rb"))
    else:
        result = dict()
    event_start_key = '__EVENT_START'
    # set/override the start of the event
    if event_start is not None:
        result[event_start_key] = event_start
    # if event start is not set, default to the beginning of today
    if event_start_key not in result:
        result[event_start_key] = get_today()
    event_start = result[event_start_key]
    for username in usernames:
        if username not in result:
            result[username] = event_start
    return result


def get_user_contributions(username: str, last_update: Dict) -> list:
    site = get_site()
    time_start = last_update[username]
    contributions = [
        {
            'page': Page(source=site, title=c['title']),
            'ns': c['ns'],
            'timestamp': parse_time(c['timestamp'], cst=True),
            'new': 'new' in c,
            'comment': c['comment'],
            'revid': c['revid']
        }
        for c in site.usercontribs(user=username, total=500)]
    last_update[username] = datetime.now(tz=CST)
    return [c for c in contributions if c['timestamp'] > time_start]


def get_user_section(username: str, parsed: WikiText) -> Section:
    for section in parsed.sections:
        if section.level == USERNAME_SECTION_LEVEL and \
                parse_section_title_username(section.title.strip()) == username:
            return section
    else:
        equals = USERNAME_SECTION_LEVEL * "="
        parsed.string = adjust_trailing_newline(parsed.string) + \
                        f"{equals} {username_to_section_title(username)} {equals}\n"
        return parsed.sections[-1]


def list_contributions(target: str, preset: str, event_start: Optional[datetime], **kwargs):
    # get list of participants
    users = get_mobilization_participants(target)
    usernames = [u.username for u in users]
    last_update = get_last_update(usernames, event_start)
    contributions_page = Page(source=get_site(), title=target + "/计分板")
    if not contributions_page.exists():
        pywikibot.error("Contributions page named " + contributions_page.title() + " does not exist.")
        return None
    parsed = wtp.parse(contributions_page.text)
    preset = get_preset(preset)
    for username in usernames:
        pywikibot.info("Processing user " + username)
        contributions = get_user_contributions(username, last_update)
        target_section = get_user_section(username, parsed)
        apply_preset(preset, contributions, target_section)
    contributions_page.text = str(parsed)
    contributions_page.save(summary="更新计分板", minor=True)
    with open(USER_CONTRIBUTION_UPDATE_FILE, "wb") as f:
        pickle.dump(last_update, f)


def run_mobilization_tally():
    dispatcher: Dict[str, Callable[..., None]] = {
        'scoreboard': update_scoreboard,
        'list_contributions': list_contributions
    }
    parser = ArgumentParser()
    parser.add_argument("command", nargs=1,
                        help="scoreboard command changes the scoreboard table; "
                             "list_contributions tracks the score of each participant.")
    parser.add_argument("target", nargs=1,
                        help="Target page of an event. Should be a user page on which you have event information.")
    parser.add_argument("-s", "--site", type=str, dest="site", default="mgp")
    parser.add_argument("-p", "--preset", type=str, dest="preset", default="vj",
                        help="Organization preset. Only applies to list_contributions."
                             "Defaults to vj. "
                             "Available options are: " + ", ".join(get_preset_names()))
    parser.add_argument("-t", "--time", dest="start", default=None,
                        help="The start time. Only applies to list_contributions. "
                             "Format as %Y-%m-%dT%H:%M:%SZ. Please use CST (+8).")
    args = parser.parse_args(sys.argv[2:])
    set_site(get_site_by_name(args.site))
    command = args.command[0]
    global USER_CONTRIBUTION_UPDATE_FILE
    USER_CONTRIBUTION_UPDATE_FILE = get_data_path().joinpath(args.preset + "_mobilization.pickle")
    start = args.start
    if start is not None:
        # start time is already in CST
        start = parse_time(start)
    if command in dispatcher:
        dispatcher[command](target=args.target[0], preset=args.preset, event_start=start)
    else:
        print(", ".join(dispatcher.keys()))
