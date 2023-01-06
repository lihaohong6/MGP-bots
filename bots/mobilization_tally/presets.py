from typing import Dict, Callable, List, Optional

import pywikibot
import wikitextparser as wtp
from pywikibot import Page

from bots.mobilization_tally.utils import adjust, count_bytes_simple, count_bytes, get_site
from utils.utils import find_templates, get_links_in_template


def contribution_filter(c, new: bool = True, ns: int = 0):
    return (not new or
            c['new'] or
            (c['minor'] and "移动页面" in c['comment'] and "[[User:" in c['comment'])) and \
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
        links = set(get_links_in_template(page))
        links = [Page(source=get_site(), title=link) for link in links]
        links_count = len(list(p for p in links if p.namespace().id == 0))
        score = links_count / 10
        return page.title(as_link=True, allow_interwiki=False) + f"（+{score}）（{links_count}个链接）"


article_cats = {
    # P主
    'VOCALOID职人', 'VOCALOID团体',
    # 歌姬
    'CeVIO角色', 'DeepVocal角色', 'Mac音角色', '袅袅虚拟歌手角色', 'Sharpkey角色', 'Synthesizer V角色', 'UTAU角色',
    'VOCALOID角色', 'VOICEROID角色', 'VocalSharp角色', 'Vogen角色', 'X Studio角色',
    # 引擎
    '歌声合成软件',
    # 演唱会
    '初音未来演唱会'}


def vj_create_producer(contribution):
    if not contribution_filter(contribution):
        return None
    page: Page = contribution['page']
    cats = get_categories(page)
    if len(list(article_cats.intersection(cats))) > 0:
        simple_count = count_bytes_simple(page.text)
        byte_count = count_bytes(page.text)
        return f"{page.title(as_link=True, allow_interwiki=False)}（+{adjust(byte_count / 200)}）" \
               f"（{simple_count}字节，调整后为{byte_count}字节）"


def get_content(rev):
    if '*' in rev:
        return rev['*']
    else:
        return rev['slots']['main']['*']


def expand_page_count_bytes(page: Page, revid: int):
    revisions = page.revisions(content=True)
    for rev in revisions:
        if rev['revid'] == revid:
            cur_content = get_content(rev)
            prev_content = get_content(next(revisions))
            break
    else:
        pywikibot.error("No revision with the desired revid found.")
        return None
    raw_byte_diff = count_bytes_simple(cur_content) - count_bytes_simple(prev_content)
    byte_diff = count_bytes(cur_content) - count_bytes(prev_content)
    if byte_diff < 0:
        byte_diff = 0
    return byte_diff, raw_byte_diff


def vj_expand_article(contribution):
    if not contribution_filter(contribution, new=False):
        return None
    page: Page = contribution['page']
    cats = get_categories(page)
    if len(list(article_cats.intersection(cats))) > 0 and '内容扩充' in contribution['comment']:
        res = expand_page_count_bytes(page, contribution['revid'])
        if res is None:
            return None
        byte_diff, raw_byte_diff = res
        if raw_byte_diff < 500:
            pywikibot.info(f"Edit with revid {contribution['revid']} on {page.title()} has {raw_byte_diff} bytes, "
                           f"lower than the thrshold. ")
            return None
        point = adjust(byte_diff / 200)
        return page.title(as_link=True, allow_interwiki=False) + \
               f"（+{point}）（增加{raw_byte_diff}字节，换算为{byte_diff}有效字节）"


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
    lyrics_kai = find_templates(wtp.parse(page.text).templates, "LyricsKai", loose=True)
    if len(lyrics_kai) != 1:
        pywikibot.error(f"Looking for translation in {page.title()}, but T:LyricsKai is not found.")
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


Preset = Dict[str, Callable[[Dict], Optional[str]]]
__presets = {
    'vj': {
        '创建歌曲': vj_create_song,
        '歌词翻译': vj_translate,
        '歌词注音': vj_furigana,
        '创建周刊': vj_vocaran,
        '创建大家族模板': vj_create_producer_template,
        '创建P主/歌姬/引擎': vj_create_producer,
        '内容扩充': vj_expand_article
    }
}


def get_preset_names() -> List[str]:
    return list(__presets.keys())


def get_preset(preset: str) -> Preset:
    if preset not in __presets:
        raise RuntimeError("Preset named " + preset + " not found.")
    return __presets[preset]
