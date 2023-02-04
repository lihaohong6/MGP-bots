import pickle
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock, Thread
from time import sleep
from typing import Tuple, List, Iterable, Dict, Set

import pywikibot
from pywikibot import Page
from pywikibot.exceptions import NoPageError
from pywikibot.page import Revision
from pywikibot.pagegenerators import PreloadingGenerator

from utils.logger import get_logger
from utils.mgp import get_page


# edit count, bytes added, articles changed
@dataclass
class ContributionInfo:
    edit_count: int = 0
    byte_count: int = 0
    pages_edited: Set[str] = field(default_factory=set)


def process_revision(old_info: ContributionInfo, revision, byte_diff: int, page_name: str) -> ContributionInfo:
    tags = revision['tags']
    if "mw-undo" in tags:
        byte_diff = 0
    return ContributionInfo(old_info.edit_count + 1,
                            old_info.byte_count + max(0, byte_diff),
                            old_info.pages_edited.union({page_name}))


# 什么年代了还在用传统锁
CONTRIBUTIONS_LOCK = Lock()


def process_page(contributions, page: Page):
    try:
        revisions: List[Revision] = list(page.revisions(reverse=True))
        prev_bytes = 0
        for revision in revisions:
            user = revision['user']
            byte_count = revision['size']
            byte_diff = byte_count - prev_bytes
            # not atomic; use a lock in case of a race condition
            CONTRIBUTIONS_LOCK.acquire()
            contributions[user] = process_revision(contributions.get(user, ContributionInfo()),
                                                   revision,
                                                   byte_diff,
                                                   page.title())
            CONTRIBUTIONS_LOCK.release()
            prev_bytes = byte_count
    except NoPageError:
        pywikibot.error(page.title() + " does not exist.")
        return


def save_contributions(contributions: dict, file_path: Path):
    with open(file_path, "wb") as f:
        # theoretically contributions is never in an inconsistent state
        # but add a lock just in case
        CONTRIBUTIONS_LOCK.acquire()
        pickle.dump(contributions, f, protocol=pickle.HIGHEST_PROTOCOL)
        CONTRIBUTIONS_LOCK.release()


def write_contributions_to_file(gen: Iterable[Page], temp_file: Path, thread_count: int = 1):
    pages = list(gen)
    completed = set()
    if not temp_file.exists():
        contributions: Dict[str, ContributionInfo] = dict()
    else:
        contributions = pickle.load(open(temp_file, "rb"))
        for contribution_info in contributions.values():
            completed.update(set(contribution_info.pages_edited))
    pywikibot.output(f"{len(pages)} pages total.")
    filtered = list(filter(lambda p: p.title() not in completed, pages))
    pywikibot.output(f"{len(filtered)} pages after filtering completed ones.")
    pywikibot.output(f"Processing contributions with {thread_count} threads.")
    threads: List[Thread] = []
    for index, page in enumerate(filtered):
        if page.title() in completed:
            pywikibot.output("Skipping " + page.title() + " since it is already done.")
            continue
        while len(threads) >= thread_count:
            sleep(0.1)
            threads = [t for t in threads if t.is_alive()]
        threads.append(Thread(target=lambda: process_page(contributions, page)))
        pywikibot.output(f"{index}/{len(filtered)} ")
        # reduce disk io since toolforge machines are slow
        if index % 20 == 0:
            save_contributions(contributions, temp_file)
    save_contributions(contributions, temp_file)

