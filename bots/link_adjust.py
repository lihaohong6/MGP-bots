import re
import urllib
from re import Match
from typing import AnyStr, Iterable, List, Callable

import pywikibot
import requests
from pywikibot import Page
from pywikibot.pagegenerators import GeneratorFactory
from urllib.parse import parse_qs, urlparse, urlunparse

LINK_END = r"[^ 　\]{<|\n]*"


def remove_link_params(link: str, predicate: Callable[[str], bool]) -> str:
    parsed = urlparse(link)
    params = parse_qs(parsed.query, keep_blank_values=False)
    parsed = list(parsed)
    parsed[4] = "&".join(f"{param}={value[0]}"
                         for param, value in params.items()
                         if predicate(param))
    result = urlunparse(parsed)
    if result.strip() == link.strip():
        return link
    if '/' == result[-1]:
        result = result[:-1]
    return result


def shorten_bb_link(match: Match):
    return remove_link_params(match.group(0), predicate=lambda s: s in ['t', 'p'])


def expand_b23(text: str) -> str:
    def fetch_real_url(match: Match):
        response = requests.get(match.group(0))
        return process_text_bb(response.url)

    return re.sub(r'https?://b23\.tv/' + LINK_END,
                  fetch_real_url,
                  text)


def process_text_bb(text: str) -> str:
    text = re.sub(r'bilibili\.com' + LINK_END,
                  shorten_bb_link,
                  text,
                  flags=re.ASCII)
    text = expand_b23(text)
    return text


def shorten_yt_link(match: Match) -> str:
    new_url = "www.youtube.com/watch?v=" + match.group(1) + match.group(2).replace("?", "&")
    return remove_link_params(new_url, lambda s: s in ['t', 'v'])


def process_text_yt(text: str) -> str:
    text = re.sub(r'youtu\.be/([\w-]+)' + '(' + LINK_END + ')',
                  shorten_yt_link,
                  text,
                  flags=re.ASCII)
    text = re.sub(r'www\.youtube\.com/watch\?v=([\w-]+)' + '(' + LINK_END + ')',
                  shorten_yt_link,
                  text,
                  flags=re.ASCII)
    return text


def search_pages(*search_strings) -> Iterable[Page]:
    from utils.sites import mgp
    gen = GeneratorFactory(site=mgp)
    gen.handle_arg('-ns:0')
    for s in search_strings:
        gen.handle_arg(f'-search:insource:"{s}"')
    return gen.getCombinedGenerator(preload=True)


def process_text(text: str) -> str:
    return process_text_bb(process_text_yt(text))


BOT_MESSAGE = "使用[[U:Lihaohong/链接清理机器人|机器人]]"


def link_adjust() -> None:
    """
    链接修复程序入口
    :return: None
    """
    for p in search_pages('spm_id_from', 'b23.tv', 'spm_id_from', 'from_spmid',
                          'share_source', 'share_medium', 'share_plat', 'share_session_id', 'share_tag', 'share_times',
                          'bbid', 'from_source', 'broadcast_type', 'is_room_feed',
                          'youtu.be'):
        result = process_text(p.text)
        if result != p.text:
            p.text = result
            p.save(summary=BOT_MESSAGE + "清理b站和YouTube链接", minor=True, tags='Bot', watch='nochange')


def link_adjust_test():
    from utils.sites import mgp
    sandbox = Page(source=mgp, title="Help:沙盒")
    sandbox.text = process_text(sandbox.text)
    sandbox.save(summary=BOT_MESSAGE + "测试清理链接", minor=True, tags="Bot")
