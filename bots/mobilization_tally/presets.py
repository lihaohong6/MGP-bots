from typing import Dict, Callable

import wikitextparser as wtp
from pywikibot import Page

from bots.mobilization_tally.utils import adjust, count_bytes_simple, count_bytes
from utils.utils import find_templates


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