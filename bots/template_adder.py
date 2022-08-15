from typing import List

import wikitextparser as wtp

from utils.logger import get_logger
from utils.mgp import get_page, MGPPage
from utils.utils import find_templates, count_trailing_newline, get_links_in_template, throttle


def add_template_to_page(page_name: str, templates: List[str]) -> bool:
    page = get_page(page_name)
    template = templates[0]
    if page is None or not page.exists():
        get_logger().info("Page named " + page_name + " does not exist.")
        return False
    parsed = wtp.parse(page.text)
    if len(find_templates(parsed.templates, *templates, loose=False)):
        get_logger().info("Template " + template + " already exists on " + page_name)
        return False
    print(page_name)
    sections = list(parsed.sections)
    target = -1
    for index, section in enumerate(sections):
        if section.title and ("注释" in section.title or "註釋" in section.title or
                              "外部链接" in section.title or "外部連結" in section.title or "外部鏈接" in section.title or
                              "参考资料" in section.title or "參考資料" in section.title):
            target = index
            break
    if target == -1:
        get_logger().error(f"Cannot find comments or external links in page {page.name} with link {page.link}")
        return False
    newline_count = count_trailing_newline(sections[target - 1].string)
    sections[target - 1].string += "\n" * max(2 - newline_count, 0) + "{{" + template + "}}\n\n"
    page.text = parsed.string
    page.save(summary="批量添加[[T:" + template + "]]", watch="watch", botflag=True, tags="Bot")
    page.open_in_browser()
    return True


def add_template(template_name: str):
    page = get_page("Template:" + template_name)
    pages = get_links_in_template(page)
    get_logger().info("Adding T:" + template_name + " to " + str(pages))
    template_names = [p.title(with_ns=False) for p in page.redirects(namespaces="Template")]
    if len(template_names) > 0:
        get_logger().info(template_name + " is also known as " + str(template_names))
    template_names.insert(0, template_name)
    for page_name in pages:
        if add_template_to_page(page_name, template_names):
            throttle(20)
        else:
            throttle(5)


def add_cat_to_page(page_name: str, cat_name: str) -> bool:
    page = get_page(page_name)
    if not page.exists():
        return False
    cats = page.categories()
    cat_names = [c.title.split(":")[1] for c in cats]
    if any([c == cat_name for c in cat_names]):
        return False
    print(page_name)


def add_category(template_name: str, cat_name: str = None):
    if cat_name is None:
        cat_name = template_name
    page = MGPPage("Template:" + template_name)
    links = get_links_in_template(page)
    for page_name in links:
        add_cat_to_page(page_name, cat_name)
        throttle(5)
