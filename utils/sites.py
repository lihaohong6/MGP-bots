from pywikibot import Site, APISite


def cm():
    return Site(fam="commons", code="commons")


def mgp() -> APISite:
    return Site(fam="mgp", code="mgp")


def mirror() -> APISite:
    return Site(fam="mirror", code="mirror")


def icu():
    return Site(fam="icu", code="icu")


def icu_cm():
    return Site(fam="icu_cm", code="icu_cm")

def enwp():
    return Site(fam="wikipedia", code="en")


def get_site_by_name(name: str):
    name_to_site = {
        'mgp': mgp,
        'mirror': mirror,
        'commons': cm
    }
    return name_to_site[name]()
