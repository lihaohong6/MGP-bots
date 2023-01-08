from unittest import TestCase

from pywikibot import Page

from bots.mobilization_tally.presets import is_vj_song
from utils.sites import mgp


class Test(TestCase):
    def test_is_vj_song(self):
        site = mgp()
        self.assertTrue(is_vj_song(Page(site, "同一夜")))
        self.assertTrue(not is_vj_song(Page(site, "中华缘木娘")))
        self.assertTrue(not is_vj_song(Page(site, "NHOT_BOT(歌曲)")))

    def test_vj_furigana(self):
        self.fail()

    def test_vj_translate(self):
        self.fail()
