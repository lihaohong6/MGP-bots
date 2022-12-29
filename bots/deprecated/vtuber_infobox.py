import re
import webbrowser

import wikitextparser as wtp
from pywikibot import Page
from pywikibot.bot import SingleSiteBot

from utils.logger import get_logger
from utils.utils import find_templates, save_continue_page, get_continue_page


class VtuberInfoboxBot(SingleSiteBot):
    def treat(self, page: Page) -> None:
        parsed = wtp.parse(page.text)
        t = find_templates(parsed.templates, "信息", "infobox", loose=True)
        if len(t) != 1:
            get_logger().error("Page " + page.title() + " has " + str(len(t)) + " info boxes.")
            return
        t = t[0]
        original = ""
        if t.get_arg("活动范围") is not None:
            original = t.get_arg("活动范围").value
        lines = page.text.split("\n")
        rules: dict = {
            'Youtube': r"https://www\.youtube\.com/channel/([a-zA-Z0-9-_]+)",
            'Bilibili': r'https://space\.bilibili\.com/([0-9]+)',
            'Acfun': r'https://www\.acfun\.cn/u/([0-9]+)',
            'Twitch': r'https://www\.twitch\.tv/([^ ]+)',
            'TikTok': r'https://www\.tiktok\.com/@([^ ]+)'
        }
        results = {}
        for line in reversed(lines):
            if "外部链接" in line and '==' in line:
                break
            if '录播' in line or '非官方' in line or '搬运' in line:
                continue
            for site in rules.keys():
                if site.lower() not in original.lower() and original != "":
                    continue
                match = re.search(rules[site], line, flags=re.I)
                if match is not None:
                    results[site] = match.group(1)
        if len(results.keys()) == 0:
            get_logger().error("No id found for " + page.title())
            return
        res = []
        for site, channel in rules.items():
            if site in results:
                res.append('{{' + site + "Link|" + results[site] + "}}")
        res = " / ".join(res)
        if t.has_arg("活动范围"):
            t.set_arg("活动范围", res)
        else:
            if t.has_arg("所属团体"):
                t.set_arg("活动范围", res, before="所属团体")
            elif t.has_arg("个人状态"):
                t.set_arg("活动范围", res, before="个人状态")
            elif t.has_arg("角色设计"):
                t.set_arg("活动范围", res, before="角色设计")
            elif t.has_arg("出身地区"):
                t.set_arg("活动范围", res, after="出身地区")
            elif t.has_arg("萌点"):
                t.set_arg("活动范围", res, after="萌点")
            get_logger().error("Cannot insert 活动范围 in " + page.title())
            return
        if page.text == str(parsed):
            get_logger().info("No changes necessary in " + page.title())
            return
        webbrowser.open(page.full_url().replace('https://mzh', 'https://zh'))
        self.userPut(page, page.text, str(parsed),
                     summary="替换活动范围", minor=True, tags="Automation tool")

    def run(self):
        save_file = "vtuber_infobox.txt"
        cont = get_continue_page(save_file)
        if cont != '!':
            for page in self.generator:
                if page.title() == cont:
                    break
        for page in self.generator:
            self.treat(page)
            save_continue_page(save_file, page.title())
        self.exit()
