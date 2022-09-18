from unittest import TestCase

from bots.isbn import treat_isbn


class TestIsbn(TestCase):
    def test_treat_isbn(self):
        text = """ISBN 978-490686622-X | {{ISBN|4718016015678}}"""
        self.assertEqual("{{ISBN|978-490686622-X}} | {{ISBN|4718016015678}}",
                         treat_isbn(text))

    def test_keep_isbn(self):
        texts = ["joijoifwjoiew", "ISBN", "ISBN 123啊"]
        for t in texts:
            self.assertEqual(t, treat_isbn(t))
