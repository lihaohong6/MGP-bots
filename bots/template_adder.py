import re
import sys
import webbrowser
from argparse import ArgumentParser
from typing import List, Any

import pywikibot
import wikitextparser as wtp
from pywikibot import Page
from pywikibot.bot import SingleSiteBot
from pywikibot.pagegenerators import GeneratorFactory

from utils.config import get_data_path, get_default_save_params
from utils.logger import get_logger
from utils.utils import find_templates, count_trailing_newline, get_links_in_template, throttle, adjust_trailing_newline


class TemplateAdderBot(SingleSiteBot):
    def __init__(self, template_name: str, open_webpage: bool, alias=None, **kwargs: Any):
        self.open_webpage = open_webpage
        page = Page(source=pywikibot.Site(), title="Template:" + template_name)
        pages = get_links_in_template(page)
        template_names = [p.title(with_ns=False) for p in page.redirects(namespaces="Template")]
        if alias is not None:
            template_names.extend(alias)
        if len(template_names) > 0:
            pywikibot.output(template_name + " is also known as " + str(template_names))
        template_names.insert(0, template_name)
        self.template_names = template_names
        page_list_path = get_data_path().joinpath("temp_page_list.txt")
        with open(page_list_path, "w") as f:
            f.write("\n".join(pages))
        gen = GeneratorFactory()
        gen.handle_arg("-ns:0")
        gen.handle_arg("-file:" + str(page_list_path.absolute()))
        super().__init__(generator=gen.getCombinedGenerator(preload=True), **kwargs)

    def treat(self, page: Page) -> None:
        template_names = self.template_names
        template = template_names[0]
        if not page.exists():
            pywikibot.output("Page named " + page.title() + " does not exist.")
            return
        parsed = wtp.parse(page.text)
        if len(find_templates(parsed.templates, *template_names, loose=False)):
            pywikibot.output("Template " + template + " already exists on " + page.title())
            return
        sections = list(parsed.sections)
        target = -1
        for index, section in enumerate(sections):
            if section.title and ("注释" in section.title or "註釋" in section.title or
                                  "外部链接" in section.title or "外部連結" in section.title or "外部鏈接" in section.title or
                                  "参考资料" in section.title or "參考資料" in section.title):
                target = index
                break
        if target == -1:
            for link in parsed.wikilinks:
                if re.search(r"\[\[(cat|category|分类):", link.string, re.IGNORECASE) is not None:
                    link.string = "{{" + template + "}}\n\n" + link.string
                    break
            else:
                pywikibot.error(f"Cannot find comments or external links or categories "
                                f"in page {page.title()} with link {page.title()}")
                return
        else:
            sections[target - 1].string = adjust_trailing_newline(sections[target - 1].string) + \
                                          "{{" + template + "}}\n\n"
        if self.open_webpage:
            webbrowser.open(page.full_url())
        self.userPut(page, page.text, parsed.string, summary="批量添加[[T:" + template + "]]",
                     **get_default_save_params(), asynchronous=True)


def add_template():
    parser = ArgumentParser()
    parser.add_argument("-o", "--open", dest="open", action="store_true",
                        help="Open the target page in a browser before an edit is made. ")
    parser.add_argument("-n", "--name", nargs=1, type=str, required=True,
                        help="Name of template to process.")
    parser.add_argument("-a", "--alias", dest="alias", nargs="*",
                        help="Aliases of this template. The program automatically detects"
                             "redirects, but cannot automatically perform conversions between"
                             "traditional and simplified Chinese. ")
    args = parser.parse_args(sys.argv[2:])
    bot = TemplateAdderBot(args.name[0], open_webpage=args.open, alias=args.alias)
    bot.run()
