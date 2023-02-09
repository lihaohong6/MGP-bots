import pickle
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from threading import Lock, Thread
from time import sleep
from typing import Tuple, List, Iterable, Dict, Set, Optional

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
    bytes_added: int = 0
    bytes_deleted: int = 0
    last_edit_date: datetime = None
    last_edit_page: str = None
    pages_edited: Set[str] = field(default_factory=set)


def process_revision(old_info: ContributionInfo, revision, byte_diff: int, page_name: str) -> ContributionInfo:
    tags = revision['tags']
    if "mw-undo" in tags or 'mw-rollback' in tags:
        byte_diff = 0
    edit_date = old_info.last_edit_date
    edit_page = old_info.last_edit_page
    if edit_date is None or revision['timestamp'] > edit_date:
        edit_date = revision['timestamp']
        edit_page = page_name
    return ContributionInfo(old_info.edit_count + 1,
                            old_info.bytes_added + max(0, byte_diff),
                            old_info.bytes_deleted - min(0, byte_diff),
                            edit_date,
                            edit_page,
                            old_info.pages_edited.union({page_name}))


# 什么年代了还在用传统锁
CONTRIBUTIONS_LOCK = Lock()


def process_page(contributions, page: Page, start_date: Optional[datetime]):
    try:
        revisions: List[Revision] = list(page.revisions(reverse=True))
        prev_bytes = 0
        for revision in revisions:
            user = revision['user']
            byte_count = revision['size']
            date = revision['timestamp']
            byte_diff = byte_count - prev_bytes
            prev_bytes = byte_count
            if start_date > date:
                continue
            # not atomic; use a lock in case of a race condition
            CONTRIBUTIONS_LOCK.acquire()
            contributions[user] = process_revision(contributions.get(user, ContributionInfo()),
                                                   revision,
                                                   byte_diff,
                                                   page.title())
            CONTRIBUTIONS_LOCK.release()
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


def write_contributions_to_file(gen: Iterable[Page], temp_file: Path, thread_count: int = 1,
                                days_before: int = None):
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
    if days_before is not None:
        start_date = datetime.now() + timedelta(days=-days_before)
    else:
        start_date = None
    for index, page in enumerate(filtered):
        if page.title() in completed:
            pywikibot.output("Skipping " + page.title() + " since it is already done.")
            continue
        while len(threads) >= thread_count:
            threads = [t for t in threads if t.is_alive()]
            sleep(0.1)
        t = Thread(target=lambda: process_page(contributions, page, start_date))
        threads.append(t)
        t.start()
        pywikibot.output(f"{index}/{len(filtered)} ")
        if thread_count == 1:
            t.join()
        # reduce disk io since toolforge machines are slow
        if index % 20 == 19:
            save_contributions(contributions, temp_file)
    save_contributions(contributions, temp_file)

