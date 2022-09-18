from pathlib import Path

data_path = Path("data")


def get_data_path() -> Path:
    return data_path


def get_lang_map():
    from pywikibot import Site
    return {
        'en': Site(code='en', fam='en'),
        'zh': Site(code='mgp', fam='mgp'),
        # 'ja': Site(fam='ja')
    }


def get_rate_limit():
    from utils.sites import mgp
    u = mgp.username()
    if "bot" in u.lower() or "机" in u:
        # FIXME: 500 will sometimes exceed the limit of 8,388,608 bytes in server response
        rate_limit = 300
    else:
        rate_limit = 50
    return rate_limit


def get_default_save_params():
    return {
        'minor': True,
        'watch': 'nochange',
        'botflag': True,
        'tags': 'Bot'
    }
