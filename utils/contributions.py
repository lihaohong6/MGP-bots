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
from utils.path_utils import EMPTY_PATH


@dataclass
class ContributionInfo:
    edit_count: int = 0
    bytes_added: int = 0
    bytes_deleted: int = 0
    pages_created: int = 0
    last_edit_date: datetime = None
    last_edit_page: str = None
    pages_edited: Set[str] = field(default_factory=set)


ContributionDict = Dict[str, ContributionInfo]


def process_revision(info: ContributionInfo, revision, byte_diff: int, page_name: str) -> ContributionInfo:
    tags = revision['tags']
    if "mw-undo" in tags or 'mw-rollback' in tags:
        byte_diff = 0
    if info.last_edit_date is None or revision['timestamp'] > info.last_edit_date:
        info.last_edit_date = revision['timestamp']
        info.last_edit_page = page_name
    info.edit_count += 1
    info.bytes_added += max(0, byte_diff)
    info.bytes_deleted -= min(0, byte_diff)
    info.pages_edited.add(page_name)
    return info


# 什么年代了还在用传统锁
CONTRIBUTIONS_LOCK = Lock()


def process_page(contributions, page: Page, start_date: Optional[datetime]):
    try:
        revisions: List[Revision] = list(page.revisions(reverse=True))
        # process all revisions with lock acquire to reduce lock overhead
        with CONTRIBUTIONS_LOCK:
            prev_bytes = 0
            for index, revision in enumerate(revisions):
                user = revision['user']
                byte_count = revision['size']
                date = revision['timestamp']
                byte_diff = byte_count - prev_bytes
                prev_bytes = byte_count
                if start_date is not None and start_date > date:
                    continue
                if index == 0:
                    contributions[user].pages_created += 1
                result = process_revision(contributions.get(user, ContributionInfo()),
                                          revision,
                                          byte_diff,
                                          page.title())
                if user not in contributions:
                    contributions[user] = result
    except NoPageError:
        pywikibot.error(page.title() + " does not exist.")
        return


def save_contributions(contributions: dict, file_path: Path):
    with open(file_path, "wb") as f:
        # theoretically contributions is never in an inconsistent state
        # but add a lock just in case
        with CONTRIBUTIONS_LOCK:
            pickle.dump(contributions, f, protocol=pickle.HIGHEST_PROTOCOL)


def get_contributions(gen: List[Page], save_path: Optional[Path] = None, thread_count: int = 1,
                      start_date: Optional[datetime] = None, existing: ContributionDict = None):
    if existing is None:
        existing = dict()
    if save_path is None:
        save_path = EMPTY_PATH
    threads = []
    for index, page in enumerate(gen):
        while len(threads) >= thread_count:
            threads = [t for t in threads if t.is_alive()]
            sleep(0.1)
        t = Thread(target=lambda: process_page(existing, page, start_date))
        threads.append(t)
        t.start()
        pywikibot.output(f"{index}/{len(gen)} ")
        if thread_count == 1:
            t.join()
        # reduce disk io since toolforge machines are slow
        if index % 20 == 19:
            save_contributions(existing, save_path)
    for t in threads:
        t.join()
    return existing


def write_contributions_to_file(gen: Iterable[Page], temp_file: Path, thread_count: int = 1,
                                days_before: int = None) -> Dict[str, ContributionInfo]:
    pages = list(gen)
    completed = set()
    if not temp_file.exists():
        contributions: ContributionDict = dict()
    else:
        contributions = pickle.load(open(temp_file, "rb"))
        for contribution_info in contributions.values():
            completed.update(set(contribution_info.pages_edited))
    pywikibot.output(f"{len(pages)} pages total.")
    filtered = list(filter(lambda p: p.title() not in completed, pages))
    pywikibot.output(f"{len(filtered)} pages after filtering completed ones.")
    pywikibot.output(f"Processing contributions with {thread_count} threads.")
    if days_before is not None:
        start_date = datetime.now() + timedelta(days=-days_before)
    else:
        start_date = None
    contributions = get_contributions(filtered, temp_file, thread_count, start_date, contributions)
    save_contributions(contributions, temp_file)
    return contributions
