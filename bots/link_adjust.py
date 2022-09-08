import re
from re import Match
from typing import Iterable, Callable, Dict
from urllib.parse import parse_qs, urlparse, urlunparse

import pywikibot
import requests
from pywikibot import Page
from pywikibot.pagegenerators import GeneratorFactory, PreloadingGenerator

LINK_END = r"""((?![ 　\]{}<|\n])[ -~])*"""


def remove_link_params(link: str, predicate: Callable[[str, str], bool]) -> str:
    """
    从链接中移除无用参数
    :param link: 链接
    :param predicate: 函数，用于判断参数是否要保留
    :return: 移除参数后的链接
    """
    parsed = urlparse(link)
    params = parse_qs(parsed.query, keep_blank_values=True)
    parsed = list(parsed)
    # avoid unnecessary changes
    if all(predicate(param, value[0]) for param, value in params.items()):
        return link
    parsed[4] = "&".join(f"{param}={value[0]}"
                         for param, value in params.items()
                         if predicate(param, value[0]))
    result = urlunparse(parsed)
    if result.strip() == link.strip():
        return link
    if '/' == result[-1]:
        result = result[:-1]
    return result


USELESS_BB_PARAMS = {
    # from C8H17OH-bot
    'from', 'seid', 'spm_id_from', 'vd_source', 'from_spmid', 'referfrom',
    'bilifrom', 'share_source', 'share_medium', 'share_plat', 'share_session_id',
    'share_tag', 'share_times', 'timestamp', 'bbid', 'ts', 'from_source', 'broadcast_type', 'is_room_feed',
    # from mall.bilibili.com link:
    # https://mall.bilibili.com/detail.html?from=mall_home_search&hasBack=false&itemsId=10040825&jumpLinkType=0
    # &msource=link&noTitleBar=1&share_medium=android&share_plat=android&share_source=COPY&share_tag=s_i
    # &timestamp=1636345640&unique_k=XlSwmO#noReffer=true&goFrom=na
    'msource', 'noTitleBar', 'hasBack', 'jumpLinkType', 'timestamp', 'unique_k', 'goFrom',
    # https://space.bilibili.com/103835/favlist?fid=61736335&ftype=create
    # https://www.bilibili.com/medialist/play/ml45827500/BV1Zs411o74K?oid=899641&otype=2
    # https://space.bilibili.com/842470/channel/seriesdetail?sid=954878&ctype=0
    'ftype', 'otype', 'ctype',
    # https://b23.tv/jf8kgOH
    'share_from', 'is_story_h5',
    # https://b23.tv/dl5XUl9
    'mid',
    # https://b23.tv/SfzFfn
    'native.theme', 'night', 'a_id', 's_id'
}

SEARCH_KEYWORDS = ['spm_id_from', 'b23.tv',
                   'from_spmid',
                   'share_source', 'share_medium', 'share_plat', 'share_session_id', 'share_tag',
                   'share_times',
                   'bbid', 'from_source', 'broadcast_type', 'is_room_feed',
                   'unique_k', 'ftype', 'otype', 'ctype',
                   'is_story_h5', 'share_from',
                   'youtu.be']


def shorten_bb_link(match: Match):
    link = match.group(0)
    if "read/mobile" in link:
        parsed = urlparse(link)
        params: Dict = parse_qs(parsed.query, keep_blank_values=False)
        if 'id' in params:
            article_id = params['id'][0]
        else:
            article_id = re.search("/([0-9]+)", parsed.path).group(1)
        return "bilibili.com/read/cv" + article_id
    return remove_link_params(link,
                              predicate=lambda k, v: k not in USELESS_BB_PARAMS
                                                     and (k != 'p' or v != '1'))


def expand_b23(text: str) -> str:
    def fetch_real_url(match: Match):
        url = match.group(0)
        response = requests.get(url)
        if response.url.strip() == url.strip():
            pywikibot.error("Link " + url + " has problematic response.")
            return url
        return process_text_bb(response.url)

    return re.sub(r'https?://b23\.tv/' + LINK_END,
                  fetch_real_url,
                  text)


def process_text_bb(text: str) -> str:
    text = re.sub(r'bilibili\.com' + LINK_END,
                  shorten_bb_link,
                  text)
    text = expand_b23(text)
    return text


USELESS_YT_PARAMS = {'feature', 'ab_channel'}


def process_text_yt(text: str) -> str:
    def expand_short_link(match: Match):
        new_url = "www.youtube.com/watch?v=" + match.group(1) + match.group(2).replace("?", "&")
        return remove_link_params(new_url, lambda s, _: s not in USELESS_YT_PARAMS)

    text = re.sub(r'youtu\.be/([\w-]+)' + '(' + LINK_END + ')',
                  expand_short_link,
                  text,
                  flags=re.ASCII)
    text = re.sub(r'(?:www\.)?youtube\.com/watch\?' + LINK_END,
                  lambda match: remove_link_params(match.group(0), lambda s, _: s not in USELESS_YT_PARAMS),
                  text)
    return text


def search_pages(*search_strings) -> Iterable[Page]:
    """
    搜索主名字空间下，源代码有任意关键词的条目
    :param search_strings: 关键词列表
    :return: Page对象
    """
    from utils.sites import mgp
    gen = GeneratorFactory(site=mgp)
    gen.handle_arg('-ns:0')
    for s in search_strings:
        gen.handle_arg(f'-search:insource:"{s}"')
    return gen.getCombinedGenerator(preload=False)


def process_text(text: str) -> str:
    return process_text_bb(process_text_yt(text))


BOT_MESSAGE = "使用[[U:Lihaohong/链接清理机器人|机器人]]"


def link_adjust() -> None:
    """
    链接修复程序入口
    :return: None
    """
    page_list = list(search_pages(*SEARCH_KEYWORDS))
    pywikibot.output(", ".join(p.title() for p in page_list))
    from utils.sites import mgp
    u = mgp.username()
    if "bot" in u.lower() or "机" in u:
        # FIXME: change rate limit to 500 here
        rate_limit = 500
    else:
        rate_limit = 50
    pages = PreloadingGenerator((p for p in page_list), rate_limit)
    for p in pages:
        try:
            result = process_text(p.text)
        except Exception as e:
            pywikibot.error(p.title() + ": " + str(e))
            continue
        if result != p.text:
            p.text = result
            p.save(summary=BOT_MESSAGE + "清理b站和YouTube链接", minor=True, tags='Bot',
                   botflag=True, watch='nochange')


def link_adjust_test():
    """
    使用沙盒测试
    :return: None
    """
    from utils.sites import mgp
    sandbox = Page(source=mgp, title="Help:沙盒")
    sandbox.text = process_text(sandbox.text)
    sandbox.save(summary=BOT_MESSAGE + "测试清理链接", minor=True, tags="Bot")
