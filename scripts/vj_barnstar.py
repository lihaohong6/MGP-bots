import os
import sys

sys.path.append(os.getcwd())
import pickle
import re
from typing import Dict

from pywikibot import Page
from pywikibot.pagegenerators import GeneratorFactory, PreloadingGenerator

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


RESULT_PATH = get_data_path().joinpath("vj.pickle")


def run_barn_star():
    p = Page(source=use_site, title="U:Lihaohong/Sandbox4")
    titles = set(re.findall(r"^[#*]\[\[([^]]+)]]", p.text, re.MULTILINE))
    pages = (Page(source=use_site, title=t) for t in titles)
    write_contributions_to_file(pages, RESULT_PATH)


def print_result():
    result: Dict[str, ContributionInfo] = pickle.load(open(RESULT_PATH, "rb"))
    usernames = sorted(result.keys(), key=lambda k: result[k].edit_count, reverse=True)
    output = """{| class="wikitable sortable"
|-
! 用户名 !! 编辑次数 !! 字节数 !! 编辑过的条目（最多显示10个）
"""
    lines = []
    for u in usernames:
        info = result[u]
        pages_edited = "、".join(list(info.pages_edited)[:])
        lines.append(f"|-\n| -{{{u}}}- || {info.edit_count} || {info.byte_count} || {pages_edited}")
    output += "\n".join(lines)
    output += "\n|}"
    print(output)


def main():
    # print_vj_list()
    if sys.argv[1] == 'run':
        run_barn_star()
    elif sys.argv[1] == 'print':
        print_result()


if __name__ == '__main__':
    main()
