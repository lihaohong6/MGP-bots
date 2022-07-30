from pathlib import Path

from pywikibot import Site

data_path = Path("data")


def get_data_path() -> Path:
    return data_path


lang_map = {
    'en': Site(code='en', fam='en'),
    'zh': Site(code='mgp', fam='mgp'),
    # 'ja': Site(fam='ja')
}
