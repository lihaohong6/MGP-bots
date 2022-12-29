# This is a sample Python script.

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.
import sys
from typing import Dict, Callable

from pywikibot import Page

from bots.boilerplate import run_boilerplate_bot
from bots.commons_image import commons_image
from bots.isbn import isbn_adjust
from bots.link_adjust import link_adjust
from bots.links_to_disambig import links_to_disambig
from bots.deprecated.mass_cat import mass_cat
from bots.mirror_sync import mirror_sync
from bots.mobilization_tally import mobilization_tally
from bots.move_image import move_image
from bots.recent_changes import patrol_recent_changes
from bots.template_adder import add_template
from bots.commons_cat import commons_cat
from bots.template_splitter import run_template_splitter
from utils.config import get_data_path
from utils.logger import setup_logger
from utils.sites import mgp


def test():
    sandbox = Page(source=mgp(), title="Help:沙盒")
    sandbox.text += "\n测试"
    sandbox.save(summary="测试", tags="Bot", minor=True)


bots: Dict[str, Callable] = {
    'mass_cat': mass_cat,
    'link_adjust': link_adjust,
    'move_image': move_image,
    'commons_image': commons_image,
    'commons_cat': commons_cat,
    'add_template': add_template,
    'boilerplate': run_boilerplate_bot,
    'isbn': isbn_adjust,
    'recent_changes': patrol_recent_changes,
    "mirror_sync": mirror_sync,
    "links_to_disambig": links_to_disambig,
    "template_splitter": run_template_splitter,
    'mobilization_tally': mobilization_tally,
    "test": test
}


def print_help():
    print("Possible options: " + ", ".join(bots.keys()))
    exit(0)


def main():
    setup_logger()
    get_data_path().mkdir(exist_ok=True)
    if len(sys.argv) == 1:
        print_help()
    command = sys.argv[1].strip()
    if command in bots:
        bots[command]()
    else:
        print("Command " + command + " not found.")
        print_help()


if __name__ == '__main__':
    main()
