import pickle

from pywikibot import Page
from pywikibot.pagegenerators import GeneratorFactory

from utils.sites import mirror
from utils.utils import find_templates

use_site = mirror()


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
    return songs.difference(set(gen.getCombinedGenerator()))


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
    expanded = mirror().expand_text(str(t))
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


def main():
    # songs = get_vj_songs()
    # rankings = get_vj_rankings()
    # producers = get_vj_producers()
    singers = get_vj_singers()
    print("\n".join("*[[" + s.title() + "]]" for s in singers))


if __name__ == '__main__':
    main()
