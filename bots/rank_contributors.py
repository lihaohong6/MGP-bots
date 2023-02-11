import pickle
import sys
from argparse import ArgumentParser
from typing import Dict, Callable

import pywikibot
from pywikibot import Page
from pywikibot.pagegenerators import GeneratorFactory, PreloadingGenerator

from utils.time_utils import cst
from utils.config import get_data_path
from utils.contributions import write_contributions_to_file, ContributionInfo
from utils.sites import mgp
from utils.utils import find_templates

use_site = mgp()


def get_vj_songs():
    gen = GeneratorFactory(site=use_site)
    gen.handle_args([
        "-ns:0",
        "-cat:使用VOCALOID的歌曲",
        "-cat:使用UTAU的歌曲",
        "-cat:使用CeVIO的歌曲",
        "-cat:使用VOICEROID的歌曲",
        "-cat:使用MUTA的歌曲",
        "-cat:使用Sharpkey的歌曲",
        "-cat:使用Synthesizer_V的歌曲",
        "-cat:使用DeepVocal的歌曲",
        "-cat:使用NEUTRINO的歌曲",
        "-cat:使用X Studio的歌曲",
        "-cat:使用ACE虚拟歌姬的歌曲",
        "-cat:使用MAIDLOID的歌曲",
        "-cat:使用初音未来 NT的歌曲"
    ])
    songs = set(gen.getCombinedGenerator())
    gen = GeneratorFactory(site=use_site)
    gen.handle_args([
        '-ns:0',
        '-cat:中国音乐作品']
    )
    gen = gen.getCombinedGenerator(preload=False)
    gen = PreloadingGenerator(gen, groupsize=500)

    def filter_songs_from_china(page: Page):
        from mgp_common.japanese import is_kana
        if len(list(filter(is_kana, page.text))) > 50:
            return False
        if "{{LyricsKai" in page.text or "{{需要翻译" in page.text or "{{求翻译" in page.text:
            return False
        return True

    subtract = set(filter(filter_songs_from_china, gen))
    return songs.difference(subtract)


def get_vj_rankings():
    gen = GeneratorFactory()
    gen.handle_args([
        '-ns:0,T',
        '-links:Template:周刊VOCAL_Character_&_UTAU_RANKING/all'
    ])
    return list(gen.getCombinedGenerator())


def get_vj_producers():
    import wikitextparser as wtp
    parsed = wtp.parse(Page(source=use_site, title="T:VOCALOID职人").text)
    t = find_templates(parsed.templates, "Navbox")
    assert len(t) == 1
    t = t[0]
    # remove Chinese producers
    t.set_arg("list1", "")
    t.set_arg("list2", "")
    t.set_arg("list3", "")
    expanded = use_site.expand_text(str(t))
    parsed = wtp.parse(expanded)
    result = []
    for link in parsed.wikilinks:
        result.append(link.title)
    return result


def get_vj_singers():
    gen = GeneratorFactory(site=use_site)
    gen.handle_args([
        '-ns:0',
        '-catr:按歌声合成软件分类'
    ])
    return list(gen.getCombinedGenerator())


def print_vj_list():
    # songs = get_vj_songs()
    # rankings = get_vj_rankings()
    # producers = get_vj_producers()
    # singers = get_vj_singers()
    # print("\n".join("*[[" + s.title() + "]]" for s in songs))
    pass


RESULT_PATH = get_data_path().joinpath("rank_contributors_info.pickle")


def run_barn_star():
    # p = Page(source=use_site, title="U:Lihaohong/Sandbox4")
    # titles = set(re.findall(r"^[#*]\[\[([^]]+)]]", p.text, re.MULTILINE))
    # pages = (Page(source=use_site, title=t) for t in titles)
    args = sys.argv[3:]
    parser = ArgumentParser()
    parser.add_argument("-d", "--days", dest="days", type=int, default=None,
                        help="Only count edits from this many days ago until now.")
    parser.add_argument("-t", "--threads", dest="threads", type=int, default=1,
                        help="Number of threads to use. Set to more than 1 under no WAF environments.")
    args, generator_args = parser.parse_known_args(args)
    if len(generator_args) == 0:
        pywikibot.error("No generator specified.")
        return
    print("Using the following arguments in generator " + " ".join(generator_args))
    gen = GeneratorFactory(site=use_site)
    gen.handle_args(generator_args)
    write_contributions_to_file(gen.getCombinedGenerator(), RESULT_PATH,
                                thread_count=args.threads, days_before=args.days)
    print_result()


def print_result():
    result: Dict[str, ContributionInfo] = pickle.load(open(RESULT_PATH, "rb"))
    usernames = sorted(result.keys(), key=lambda k: result[k].edit_count, reverse=True)
    output = """{| class="wikitable sortable"
|-
! 用户名 !! 编辑次数 !! 增加字节数 !! 删除字节数 !! 最后一次编辑 !! 最后一次编辑的条目
"""
    lines = []
    known_bots = {
        "AnnAngela-abot", "AnnAngela-bbot", "AnnAngela-bot", "AnnAngela-cbot", "AnnAngela-dbot", "Bhsd-bot",
        "C8H17OH-bot", "Delete page script", "Eizenchan", "LihaohongBot", "SinonJZH-bot", "UNC HA Bot", "XzonnBot",
        "星海-adminbot", "星海-interfacebot", "星海-oversightbot", "机娘史蒂夫", "机娘星海酱", "机娘鬼影233号", "滥用过滤器",
        "萌百娘", "重定向修复器",

        "Swampland Robot", "Funce"
    }
    for bot in known_bots:
        if bot in usernames:
            usernames.remove(bot)
    for username in usernames:
        info = result[username]
        lines.append(f"|-\n| -{{{username}}}- || {info.edit_count} || {info.bytes_added} || {info.bytes_deleted} || "
                     f"{info.last_edit_date.astimezone(cst).strftime('%y-%m-%d %H:%M')} || {info.last_edit_page}")
    output += "\n".join(lines)
    output += "\n|}"
    print(output)


def reset():
    RESULT_PATH.unlink(missing_ok=True)


def rank_contributors():
    dispatcher: Dict[str, Callable] = {
        'run': run_barn_star,
        'print': print_result,
        'reset': reset
    }
    if len(sys.argv) <= 2:
        print("Too few arguments.")
        return
    cmd = sys.argv[2]
    if cmd in dispatcher:
        dispatcher[sys.argv[2]]()
    else:
        print("Invalid command.")
        print(", ".join(dispatcher.keys()))


if __name__ == '__main__':
    rank_contributors()
