import re
import sys
from typing import Dict, Set

import pywikibot
import wikitextparser as wtp
from pywikibot import Page
from wikitextparser import WikiText

from bots.mobilization_tally.utils import adjust, get_site


def parse_section_title_username(title: str) -> str:
    parsed = wtp.parse(title)
    username = parsed.wikilinks[0].text
    return username


Graph = Dict[str, Set[str]]


def topological_sort(graph: Graph):
    in_deg = dict((node, 0) for node in graph.keys())
    for node, neighbors in graph.items():
        for neighbor in neighbors:
            in_deg[neighbor] += 1
    remaining = set(graph.keys())
    result = []
    while len(remaining) > 0:
        remove = set()
        for node in remaining:
            if in_deg[node] == 0:
                for neighbor in graph[node]:
                    in_deg[neighbor] -= 1
                remove.add(node)
                result.append(node)
        remaining.difference_update(remove)
        if len(remove) == 0:
            pywikibot.warn("Topological sort failed: loop detected.")
            result = list(graph.keys())
            break
    return result


USERNAME_SECTION_LEVEL = 2
SCORE_SECTION_LEVEL = 3


def get_scoreboard_columns(parsed: WikiText):
    graph = dict()
    prev = None
    for section in parsed.sections:
        if section.level == USERNAME_SECTION_LEVEL:
            prev = None
        if section.level == SCORE_SECTION_LEVEL:
            cur = section.title.strip()
            if cur not in graph:
                graph[cur] = set()
            if prev is not None:
                graph[prev].add(cur)
            prev = cur
    return topological_sort(graph)


def update_scoreboard(target: str, **kwargs):
    contributions_page = Page(source=get_site(), title=target + "/计分板")
    scoreboard_page = Page(source=get_site(), title=target + "/排行榜")
    for p in [contributions_page, scoreboard_page]:
        if not p.exists():
            pywikibot.error("Page titled " + p.title() + " does not exist. Double check your configs.")
            return None
    parsed = wtp.parse(contributions_page.text)
    current_user = None
    # get scoreboard
    scoreboard: Dict[str, Dict[str, float]] = dict()
    scoreboard_columns = get_scoreboard_columns(parsed)
    for section in parsed.sections:
        if section.level == USERNAME_SECTION_LEVEL:
            current_user = parse_section_title_username(section.title.strip())
            scoreboard[current_user] = dict((column, 0) for column in scoreboard_columns)
        elif section.level == SCORE_SECTION_LEVEL:
            lines = str(section).splitlines()
            for line in lines:
                score = re.search(r"[(（]\+([0-9.]+)[)）]", line)
                if score is not None:
                    scoreboard[current_user][section.title.strip()] += float(score.group(1))

    # tally total score for each user and sort based on score (ties are broken based on username)
    SCORE_COLUMN = "总分"
    scoreboard_columns.append(SCORE_COLUMN)
    for user in scoreboard:
        scoreboard[user][SCORE_COLUMN] = adjust(sum(score for score in scoreboard[user].values()))
    user_ranking = sorted(scoreboard.keys(),
                          key=lambda username: (-scoreboard[username][SCORE_COLUMN], username))

    # convert scoreboard to wikitable
    table = ["{| class=\"wikitable sortable\"",
             "|-",
             "! 排名 !! 用户名 !! " + " !! ".join(scoreboard_columns)]
    for ranking, user in enumerate(user_ranking):
        row = scoreboard[user]
        table.append("|-")
        line = f"| {ranking + 1} || -{{[[U:{user}|{user}]]}}- || " + \
               " || ".join(str(adjust(row[column_name]))
                           for column_name in scoreboard_columns)
        table.append(line)
    # the last row is an unsortable row to calculate the total score
    table.append("|- class=\"sortbottom\"")
    totals = []
    for column_name in scoreboard_columns:
        total = sum(individual_scores[column_name]
                    for individual_scores in scoreboard.values())
        totals.append(str(adjust(total)))
    table.append("! 总和 !! !! " + " !! ".join(totals))
    table.append("|}")

    # find the appropriate section to edit on the page
    parsed = wtp.parse(scoreboard_page.text)
    target = None
    for section in parsed.sections:
        if section.level != 0:
            target = section
            break
    if target is None:
        print("Cannot find an appropriate section for the scoreboard. "
              "Please ensure that there is at least one section with level 2 or more on " +
              scoreboard_page.title())
        return
    target.contents = "\n" + "\n".join(table)
    scoreboard_page.text = str(parsed)
    scoreboard_page.save(summary="更新排行榜", minor=True, tags="Bot")
