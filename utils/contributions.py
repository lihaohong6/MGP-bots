import pickle
from pathlib import Path
from typing import Tuple, List, Iterable, Dict

from pywikibot.page import Revision

from utils.logger import get_logger
from utils.mgp import get_page

# edit count, bytes added, articles changed
ContributionInfo = Tuple[int, int, List[str]]


def process_revision(old_info: ContributionInfo, revision, byte_diff: int, page_name: str) -> ContributionInfo:
    tags = revision['tags']
    if "mw-undo" in tags:
        byte_diff = 0
    prev_edits, prev_bytes, prev_list = old_info
    if page_name not in prev_list:
        prev_list.append(page_name)
    return prev_edits + 1, prev_bytes + max(0, byte_diff), prev_list


def process_page(contributions, page_name):
    page = get_page(page_name)
    if page.exists() and page.namespace().id == 0:
        revisions: List[Revision] = list(page.revisions(reverse=True))
        prev_bytes = 0
        for revision in revisions:
            user = revision['user']
            byte_count = revision['size']
            byte_diff = prev_bytes - byte_count
            contributions[user] = process_revision(contributions.get(user, (0, 0, [])),
                                                   revision,
                                                   byte_diff,
                                                   page_name)
            prev_bytes = byte_count


def write_contributions_to_file(gen: Iterable[str], temp_file: Path):
    pages = list(gen)
    completed = set()
    if not temp_file.exists():
        contributions: Dict[str, ContributionInfo] = dict()
    else:
        contributions = pickle.load(open(temp_file, "rb"))
        for byte_count, pages in contributions.values():
            completed.union(set(pages))
    for index, page_name in enumerate(pages):
        if page_name in completed:
            continue
        process_page(contributions, page_name)
        get_logger().info(f"{index}/{len(pages)} ")
        with open(temp_file, "wb") as f:
            pickle.dump(contributions, f, protocol=pickle.HIGHEST_PROTOCOL)
