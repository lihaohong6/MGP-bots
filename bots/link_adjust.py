import re
from re import Match
from typing import AnyStr, Iterable, List

import pywikibot
import requests
from pywikibot import Page
from pywikibot.pagegenerators import GeneratorFactory
from urllib.parse import parse_qs, urlparse

LINK_END = r"[^ 　\]{<|]*"


def get_link_params(link: str, targets: List[str], prepend: str = '?') -> str:
    parsed = urlparse(link)
    params = parse_qs(parsed.query, keep_blank_values=False)
    result = "&".join(f"{param}={value[0]}" for param, value in params.items() if param in targets)
    if result.strip() != "":
        return prepend + result
    return ""


def shorten_bb_link(match: Match):
    return match.group(1) + get_link_params(match.group(0), targets=['t', 'p'], prepend="?")


def expand_b23(text: str) -> str:
    def fetch_real_url(match: Match):
        response = requests.get(match.group(0))
        return process_text_bb(response.url)

    return re.sub(r'https?://b23\.tv/' + LINK_END,
                  fetch_real_url,
                  text)


def process_text_bb(text: str) -> str:
    text = re.sub(r'(www\.bilibili\.com/video/BV[0-9A-Za-z]{10})' + LINK_END,
                  shorten_bb_link,
                  text,
                  flags=re.ASCII)
    text = re.sub(r'(www\.bilibili\.com/read/cv[0-9]+)' + LINK_END,
                  shorten_bb_link,
                  text,
                  flags=re.ASCII)
    text = re.sub(r'((?:live|t|space)\.bilibili\.com/[0-9]+)' + LINK_END,
                  r'\1',
                  text,
                  flags=re.ASCII)
    text = expand_b23(text)
    return text


def shorten_yt_link(match: Match) -> str:
    return "www.youtube.com/watch?v=" + match.group(1) + \
           get_link_params(match.group(0), targets=['t'], prepend='&')


def process_text_yt(text: str) -> str:
    text = re.sub(r'youtu\.be/([\w-]+)' + LINK_END,
                  shorten_yt_link,
                  text,
                  flags=re.ASCII)
    text = re.sub(r'www\.youtube\.com/watch\?v=([\w-]+)' + LINK_END,
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


def link_adjust():
    for p in search_pages('spm_id_from', 'b23.tv', 'spm_id_from', 'from_spmid',
                          'share_source', 'share_medium', 'share_plat', 'share_session_id', 'share_tag', 'share_times',
                          'bbid', 'from_source', 'broadcast_type', 'is_room_feed',
                          'youtu.be'):
        p.text = process_text(p.text)
        p.save(summary=BOT_MESSAGE + "清理b站和YouTube链接", minor=True, tags='Bot', watch='nochange')


def link_adjust_test():
    from utils.sites import mgp
    sandbox = Page(source=mgp, title="Help:沙盒")
    sandbox.text = process_text(sandbox.text)
    sandbox.save(summary=BOT_MESSAGE + "测试清理链接", minor=True, tags="Bot")
