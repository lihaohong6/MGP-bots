# This is a sample Python script.

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.
import sys
from typing import Dict, Callable

from bots.boilerplate import run_boilerplate_bot
from bots.commons_image import commons_image
from bots.isbn import isbn_adjust
from bots.link_adjust import link_adjust
from bots.mass_cat import mass_cat
from bots.move_image import move_image
from bots.recent_changes import patrol_recent_changes
from bots.template_adder import add_template
from bots.vtuber_commons_cat import vtuber_commons_cat
from utils.config import get_data_path
from utils.logger import setup_logger

bots: Dict[str, Callable] = {
    'mass_cat': mass_cat,
    'link_adjust': link_adjust,
    'move_image': move_image,
    'commons_image': commons_image,
    'vtuber_commons_cat': vtuber_commons_cat,
    'add_template': add_template,
    'boilerplate': run_boilerplate_bot,
    'isbn': isbn_adjust,
    'recent_changes': patrol_recent_changes
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
