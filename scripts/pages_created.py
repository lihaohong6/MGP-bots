import pickle
import sys
from pathlib import Path

import init_script
from pywikibot.pagegenerators import GeneratorFactory

from utils.sites import mgp

site = mgp()


def get_all_pages():
    page_file = Path("data/all_vocaloid_songs.pickle")
    if not page_file.exists():
        cats = {'使用VOCALOID的歌曲', '使用UTAU的歌曲', '使用CeVIO的歌曲', '使用初音未来 NT的歌曲',
                '使用DeepVocal的歌曲', '使用MAIDLOID的歌曲',
                '使用MUTA的歌曲', '使用NEUTRINO的歌曲', '使用袅袅虚拟歌手的歌曲', '使用Sharpkey的歌曲',
                '使用Synthesizer V的歌曲', '使用VOICEROID的歌曲',
                '使用VOICEVOX的歌曲', '使用VocalSharp的歌曲', '使用X Studio的歌曲'}
        gen = GeneratorFactory()
        gen.handle_args(["-cat:" + c for c in cats] + ['-ns:0'])
        gen = gen.getCombinedGenerator()
        result = [p.title() for p in gen]
        pickle.dump(result, open(page_file, "wb"))
    else:
        result = pickle.load(open(page_file, "rb"))
    return result


all_pages = set(get_all_pages())

pages_created = [c['title']
                 for c in site.usercontribs(user=sys.argv[1], namespaces=0)
                 if 'new' in c and c['title'] in all_pages]
print("\n".join(reversed([p for p in pages_created])))
