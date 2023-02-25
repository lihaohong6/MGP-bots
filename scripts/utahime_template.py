import pickle
import re
from textwrap import indent
from typing import Optional, List

from bs4 import BeautifulSoup
from mgp_common.string_utils import auto_lj

import init_script
from datetime import datetime
from enum import Enum

from pywikibot import Page
from pywikibot.pagegenerators import GeneratorFactory, PreloadingGenerator
from wikitextparser import parse, Template

from dataclasses import dataclass

from utils.config import get_data_path
from utils.sites import mgp, mirror
from utils.utils import find_templates


class Status(Enum):
    LEGENDARY = "传说曲",
    TEMPLE = "殿堂曲",
    NONE = "其它",


@dataclass
class Song:
    name_ja: str
    name_zh: str
    name_link: str
    cover: bool
    date: datetime
    status: Status


site = mirror()


def get_temple_songs(color):
    result = []
    for year in range(2007, 2023):
        page = Page(source=site, title=f"VOCALOID殿堂曲/{year}年投稿")
        parsed = parse(page.text)
        songs = find_templates(parsed.templates, "Temple Song")
        for s in songs:
            if not s.has_arg("color") or not s.get_arg("color").value.strip() == color:
                continue
            entry = s.get_arg("条目")
            if entry is None:
                entry = s.get_arg("曲目")
            link = entry.wikilinks[0]
            date = s.get_arg("投稿日期")
            if date is None:
                date = s.get_arg("投稿时间")
            date = date.value.strip().split(" ")[0]
            date = datetime.strptime(date, "%Y-%m-%d")
            result.append(Song(
                name_ja="",
                name_zh=link.text,
                name_link=link.title,
                cover=re.search("[(（]翻[)）]", entry.value) is not None,
                date=date,
                status=Status.LEGENDARY if s.has_arg("传说") else Status.TEMPLE
            ))
    gen = PreloadingGenerator(Page(source=site, title=s.name_link) for s in result)
    ret = []
    for index, page in enumerate(gen):
        p = parse_page(page)
        if p is not None:
            ret.append(p)
        else:
            ret.append(result[index])
    return ret


def parse_page(page: Page) -> Optional[Song]:
    if page.text.strip() == "":
        return None
    if page.text[0] == '#' and page.isRedirectPage():
        page = page.getRedirectTarget()
    parsed = parse(page.text)
    song_boxes = find_templates(parsed.templates, "VOCALOID_Songbox")
    if len(song_boxes) == 0:
        print(page.title())
        return None
    song_box = song_boxes[0]
    names = song_box.get_arg("歌曲名称").value
    parts = re.split("<br */?>", names)
    candidates = []
    name_ja = None
    for part in parts:
        # remove html tags such as <span>
        part = parse(BeautifulSoup(part.strip(), "html.parser").text)
        lj = find_templates(part.templates, "lj")
        if len(lj) > 0:
            name_ja = lj[0].get_arg("1").value
            break
        lang = find_templates(parsed.templates, "lang")
        if len(lang) > 0:
            name_ja = lang[0].get_arg("2").value
            break
        candidates.append(str(part))
    if name_ja is None:
        name_ja = candidates[0]
    if len(find_templates(parsed.templates, "VOCALOID殿堂曲题头")) > 0:
        status = Status.TEMPLE
    elif len(find_templates(parsed.templates, "VOCALOID传说曲题头")) > 0:
        status = Status.LEGENDARY
    else:
        status = Status.NONE
    possible_args = ["投稿时间", '投稿時間', "其他资料", "其他資料"]
    for arg in possible_args:
        date_text = song_box.get_arg(arg)
        if date_text is not None:
            break
    else:
        print(page.title())
        return
    dates = re.findall(r"([0-9]{4})年([0-9]{1,2})月([0-9]{1,2})[日号]",
                       date_text.value)
    song_date = datetime(1900, 1, 1)
    for date in dates:
        date = datetime(year=int(date[0]), month=int(date[1]), day=int(date[2]))
        if song_date.year == 1900 or song_date > date:
            song_date = date
    return Song(name_ja=name_ja,
                name_zh="",
                name_link=page.title(),
                cover=False,
                date=song_date,
                status=status)


def get_songs_in_cat(name):
    gen = GeneratorFactory()
    gen.handle_args([f"-cat:{name}歌曲", "-ns:0"])
    gen = gen.getCombinedGenerator(preload=True)
    return [parse_page(p) for p in gen]


def song_to_link(s: Song):
    if s.name_ja.strip() != "":
        text = s.name_ja
    else:
        text = s.name_zh
    append = ""
    if s.cover:
        append = "（翻）"
    if text == s.name_link or text is None or text.strip() == "":
        return f"[[{s.name_link}]]" + append
    return f"[[{s.name_link}|{auto_lj(text)}]]" + append


def to_navbox(songs: List[Song]) -> str:
    r = Template("{{Navbox\n}}")
    index = 1
    for status in [Status.LEGENDARY, Status.TEMPLE, Status.NONE]:
        s = [s for s in songs if s.status == status]
        if len(s) == 0:
            continue
        r.set_arg(f"group{index}", str(status.value[0]))
        r.set_arg(f"list{index}", to_subgroup(s))
        index += 1
    return str(r)


def to_subgroup(songs: List[Song]):
    r = Template("{{Navbox_subgroup\n}}")
    year_dict = dict()
    for s in songs:
        lst = year_dict.get(s.date.year, [])
        lst.append(s)
        year_dict[s.date.year] = lst
    for index, year in enumerate(sorted(year_dict.keys())):
        r.set_arg(f"group{index + 1}", str(year))
        r.set_arg(f"list{index + 1}", " • ".join(song_to_link(song) for song in year_dict[year]))
    return str(r)


def main():
    name = "Megpoid"
    color = "#CCFF00"
    SONG_FILE = get_data_path().joinpath("utahime_template.pickle")
    if SONG_FILE.exists():
        songs = pickle.load(open(SONG_FILE, "rb"))
    else:
        result = get_temple_songs(color) + get_songs_in_cat(name)
        result = [s for s in result if s is not None]
        existing = set()
        songs = []
        for s in result:
            if s.name_link not in existing:
                existing.add(s.name_link)
                songs.append(s)
        pickle.dump(songs, open(SONG_FILE, "wb"))
    print(to_navbox(songs))


if __name__ == "__main__":
    main()
