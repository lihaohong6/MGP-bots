from unittest import TestCase

from bots.disambiguator import disambiguate_page_text


class Test(TestCase):
    def test_disambiguate_page_text(self):
        d = disambiguate_page_text
        r = d(text="[[A B#C|D]]",
              choices=["A1", "A2"],
              replace={"A B"},
              test=[2])
        self.assertEqual("[[A2#C|D]]", r)
        r = d(text="[[冒险岛]]",
              choices=["A", "B"],
              replace={"冒险岛"},
              test=[1])
        self.assertEqual("[[A|冒险岛]]", r)
