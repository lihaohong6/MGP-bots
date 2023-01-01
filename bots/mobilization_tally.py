import re
import sys
from argparse import ArgumentParser
from datetime import datetime, timedelta
from typing import Dict, Callable, Set, List

import wikitextparser as wtp
from pywikibot import APISite, Page, User
from wikitextparser import WikiText, Section

from utils.sites import get_site_by_name
from utils.utils import adjust_trailing_newline, find_templates

site: APISite


def parse_section_title_username(title: str) -> str:
    parsed = wtp.parse(title)
    username = parsed.wikilinks[0].text
    return username


def username_to_section_title(username: str) -> str:
    return "-{[[U:" + username + "|" + username + "]]}-"


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
            print("Topological sort failed: loop detected.", file=sys.stderr)
            result.extend(list(remaining))
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
    contributions_page = Page(source=site, title=target + "/计分板")
    scoreboard_page = Page(source=site, title=target + "/排行榜")
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
    scoreboard_page.save(summary="更新排行榜（试运行）", minor=True, tags="Bot")


def contribution_filter(c, new: bool = True, ns: int = 0):
    return (not new or
            'new' in c or
            ('minor' in c and "移动页面" in c['comments'] and "[[User:" in c['comments'])) and \
           c['ns'] == ns


def get_categories(page: Page):
    return set(c.title(with_ns=False) for c in page.categories())


def vj_create_song(contribution):
    if not contribution_filter(contribution):
        return None
    page: Page = contribution['page']
    categories = get_categories(page)
    engines = {'使用VOCALOID的歌曲', '使用UTAU的歌曲', '使用CeVIO的歌曲', '使用初音未来 NT的歌曲', '使用DeepVocal的歌曲', '使用MAIDLOID的歌曲',
               '使用MUTA的歌曲', '使用NEUTRINO的歌曲', '使用袅袅虚拟歌手的歌曲', '使用Sharpkey的歌曲', '使用Synthesizer V的歌曲', '使用VOICEROID的歌曲',
               '使用VOICEVOX的歌曲', '使用VocalSharp的歌曲', '使用X Studio的歌曲', '使用的歌曲'}
    if len(categories.intersection(engines)) == 0:
        return None
    if '中国音乐作品' in categories:
        return None
    return page.title(as_link=True, allow_interwiki=False) + "（+1）"


def vj_create_producer_template(contribution):
    if not contribution_filter(contribution, ns=10):
        return None
    page: Page = contribution['page']
    cats = get_categories(page)
    if '虚拟歌手音乐人模板' in cats:
        links_count = len(list(p for p in page.linkedPages() if p.namespace().id == 0))
        score = links_count / 5
        return page.title(as_link=True, allow_interwiki=False) + f"（+{score}）（{links_count}个链接）"


def count_bytes_simple(text: str) -> int:
    return len(text.encode('utf-8'))


def count_bytes(text: str) -> int:
    initial = count_bytes_simple(text)
    parsed = wtp.parse(text)
    templates = ['Producer_Song', 'Album Infobox', 'Tracklist']
    subtract = []
    for t in templates:
        template_bytes = 0
        for found in find_templates(parsed.templates, t):
            template_bytes += count_bytes_simple(str(found))
        subtract.append(template_bytes)
    return round(initial - sum(subtract) / 2)


def vj_create_producer(contribution):
    if not contribution_filter(contribution):
        return None
    page: Page = contribution['page']
    cats = get_categories(page)
    if 'VOCALOID职人' in cats or 'VOCALOID团体' in cats:
        simple_count = count_bytes_simple(page.text)
        byte_count = count_bytes(page.text)
        return f"{page.title(as_link=True, allow_interwiki=False)}（+{adjust(byte_count / 200)}）" \
               f"（{simple_count}字节，调整后{byte_count}字节）"


def vj_furigana(contribution):
    if not contribution_filter(contribution, new=False):
        return None
    page: Page = contribution['page']
    if '歌词注音' in contribution['comment']:
        return page.title(as_link=True, allow_interwiki=False) + "（+0.2）"


def vj_translate(contribution):
    if not contribution_filter(contribution, new=False):
        return None
    page: Page = contribution['page']
    if '翻译歌词' not in contribution['comment']:
        return None
    lyrics_kai = find_templates(wtp.parse(page.text).templates, "LyricsKai")
    if len(lyrics_kai) != 1:
        return None
    lyrics_kai = lyrics_kai[0]
    translation = lyrics_kai.get_arg("translated")
    if translation is None:
        return None
    byte_count = count_bytes_simple(translation.value)
    return page.title(as_link=True, allow_interwiki=False) + f"（+{adjust(byte_count / 150)}）（{byte_count}字节）"


def vj_vocaran(contribution):
    if not contribution_filter(contribution):
        return None
    page: Page = contribution['page']
    cats = get_categories(page)
    if '周刊VOCAL Character & UTAU排行榜' in cats:
        return page.title(as_link=True, allow_interwiki=False) + "（+25）"


Preset = Dict[str, Callable]


def adjust(num: float):
    return round(num, 2)


def get_preset(preset: str) -> Preset:
    presets = {
        'vj': {
            '创建歌曲': vj_create_song,
            '歌词翻译': vj_translate,
            '歌词注音': vj_furigana,
            '创建周刊': vj_vocaran,
            '创建大家族模板': vj_create_producer_template,
            '创建P主': vj_create_producer,
        }
    }
    if preset not in presets:
        raise RuntimeError("Preset named " + preset + " not found.")
    return presets[preset]


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
    signup_page = Page(source=site, title=target + "/报名")
    parsed = wtp.parse(signup_page.text)
    section = parsed.sections[1]
    return [User(source=site, title=link.title)
            for link in section.wikilinks
            if link.title[0] == 'U']


def list_contributions(target: str, preset: str, **kwargs):
    # get list of participants
    users = get_mobilization_participants(target)
    print("Participants: " + ", ".join(u.username for u in users))

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


def mobilization_tally():
    parser = ArgumentParser()
    parser.add_argument("command", nargs=1)
    parser.add_argument("target", nargs=1)
    parser.add_argument("-s", "--site", type=str, dest="site", default="mgp")
    parser.add_argument("-p", "--preset", type=str, dest="preset", default="vj")
    args = parser.parse_args(sys.argv[2:])
    global site
    site = get_site_by_name(args.site)
    dispatcher: Dict[str, Callable[..., None]] = {
        'scoreboard': update_scoreboard,
        'list_contributions': list_contributions
    }
    command = args.command[0]
    if command in dispatcher:
        dispatcher[command](target=args.target[0], preset=args.preset)
    else:
        print(", ".join(dispatcher.keys()))
