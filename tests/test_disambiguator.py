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

    def test_disambiguate_vocaloid_template(self):
        test_template = """{{{{VOCALOID_&_UTAU_Ranking/bricks
|曲名 = Divide{}
|翻唱 = 
|本周 = 11
}}}}"""
        original = test_template.format("")
        d = disambiguate_page_text
        changed = d(original, choices=['Divide(初音未来)', 'DIVIDE(镜音铃)'], replace={'Divide'},
                    test=[1])
        self.assertEqual(test_template.format("\n|后缀 = (初音未来)"), changed)
        changed = d(original, choices=['Divide(初音未来)', 'DIVIDE(镜音铃)'], replace={'Divide'},
                    test=[2])
        self.assertEqual(test_template.format("\n|条目 = DIVIDE(镜音铃)"), changed)
