from pywikibot import Site, APISite


def cm():
    return Site(fam="commons", code="commons")


def mgp() -> APISite:
    return Site(fam="mgp", code="mgp")


def mirror():
    return Site(fam="mirror", code="mirror")


def get_site_by_name(name: str):
    name_to_site = {
        'mgp': mgp,
        'mirror': mirror,
        'commons': cm
    }
    return name_to_site[name]()
