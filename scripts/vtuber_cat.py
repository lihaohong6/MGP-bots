from pywikibot import Page
from pywikibot.pagegenerators import GeneratorFactory, PreloadingGenerator

from utils.config import get_data_path
from utils.sites import mgp, cm


def main():
    gen = GeneratorFactory(site=mgp())
    gen.handle_args(["-cat:虚拟UP主", "-ns:0"])
    gen = gen.getCombinedGenerator()
    titles = ("Category:" + p.title() for p in gen)
    gen = PreloadingGenerator((Page(source=cm(), title=t) for t in titles))
    for p in gen:
        if not p.exists() or "虚拟" not in p.text:
            print(p.title())


if __name__ == "__main__":
    main()
