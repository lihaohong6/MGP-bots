import pickle
from dataclasses import dataclass, field
from pathlib import Path
from typing import Tuple, List, Iterable, Dict, Set

from pywikibot import Page
from pywikibot.page import Revision

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


def process_page(contributions, page: Page):
    if page.exists() and page.namespace().id == 0:
        revisions: List[Revision] = list(page.revisions(reverse=True))
        prev_bytes = 0
        for revision in revisions:
            user = revision['user']
            byte_count = revision['size']
            byte_diff = byte_count - prev_bytes
            contributions[user] = process_revision(contributions.get(user, ContributionInfo()),
                                                   revision,
                                                   byte_diff,
                                                   page.title())
            prev_bytes = byte_count


def write_contributions_to_file(gen: Iterable[Page], temp_file: Path):
    pages = list(gen)
    completed = set()
    if not temp_file.exists():
        contributions: Dict[str, ContributionInfo] = dict()
    else:
        contributions = pickle.load(open(temp_file, "rb"))
        for contribution_info in contributions.values():
            completed.update(set(contribution_info.pages_edited))
    for index, page in enumerate(pages):
        if page.title() in completed:
            continue
        process_page(contributions, page)
        get_logger().info(f"{index}/{len(pages)} ")
        with open(temp_file, "wb") as f:
            pickle.dump(contributions, f, protocol=pickle.HIGHEST_PROTOCOL)
