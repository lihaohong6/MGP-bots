from abc import ABC
from typing import Any, Iterable, Optional

from pywikibot import Page
from pywikibot.bot import SingleSiteBot
from pywikibot.pagegenerators import GeneratorFactory

from utils.config import get_data_path


class ResumableBot(SingleSiteBot, ABC):

    def __init__(self, bot_name: str, generator: Iterable[Page], initial_state: Optional[Any]):
        self.bot_name = bot_name
        self.generator = generator
        self.state = initial_state
        bot_directory = get_data_path().joinpath(bot_name)
        bot_directory.mkdir(exist_ok=True, parents=True)
        page_list = bot_directory.joinpath("page_list.txt")
        continue_file = bot_directory.joinpath("continue_page.txt")
        # TODO: use continue file
        if page_list.exists():
            gen = GeneratorFactory()
            gen.handle_arg("-file:" + str(page_list.absolute()))
            self.generator = gen.getCombinedGenerator(preload=True)

    def save_progress(self):
        pass
