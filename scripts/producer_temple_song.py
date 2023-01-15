import sys
import init_script

from mgp_common.video import VideoSite
from wikitextparser import parse

from pywikibot import Page
from mgp_common import video

from utils.sites import mgp
from utils.utils import find_templates


def main():
    page = sys.argv[1]
    page = Page(source=mgp(), title=page)
    parsed = parse(page.text)
    songs = find_templates(parsed.templates, "Producer_Song")
    TEMPLE, LEGENDARY = 100000, 1000000
    legendary = 0
    temple = 0
    for s in songs:
        nnd = s.get_arg("nnd_id")
        if nnd is None:
            continue
        nnd = nnd.value.strip()
        if nnd == "":
            continue
        nnd_video = video.video_from_site(site=VideoSite.NICO_NICO, identifier=nnd)
        if nnd_video is None:
            continue
        views = nnd_video.views
        if TEMPLE <= views < LEGENDARY:
            temple += 1
        elif views >= LEGENDARY:
            legendary += 1
    print(f"Temple: {temple} + {legendary} = {temple + legendary}.\nLegendary: {legendary}.")


if __name__ == "__main__":
    main()
