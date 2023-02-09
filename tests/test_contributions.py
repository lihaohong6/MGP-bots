from datetime import datetime, timedelta
from pathlib import Path
from unittest import TestCase

from pywikibot import Page

from utils.contributions import write_contributions_to_file, get_contributions
from utils.path_utils import EMPTY_PATH
from utils.sites import mgp


class Test(TestCase):
    def test_write_contributions_to_file(self):
        # not a reliable test; consider using a page on mirror
        gen = [Page(source=mgp(), title="碧蓝航线")]
        c = get_contributions(gen, Path(EMPTY_PATH), 1)
        self.assertTrue(len(c.keys()) > 10)
        c = get_contributions(gen, Path(EMPTY_PATH), 10, datetime.now() + timedelta(days=-100))
        self.assertTrue(len(c.keys()) > 0)
