# This is a sample Python script.
import pickle
# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import re
from pathlib import Path
from queue import Queue, Empty
from threading import Thread

from pywikibot import Page, APISite, FilePage
from pywikibot.data.api import QueryGenerator

from utils.sites import mirror, icu, cm, icu_cm


def should_download(page_title: str) -> bool:
    return re.search(r"\.(gif|jpg|jpeg|png|svg|webp)$", page_title, re.IGNORECASE) is not None


def process_batch(page_list: list):
    queue = Queue()
    s: APISite = mirror()
    s.login()
    for p in page_list:
        queue.put(p)

    def upload_worker():
        while True:
            if queue.empty():
                return
            try:
                page = queue.get(timeout=0.1)
            except Empty:
                return
            try:
                page: FilePage
                s.upload(filepage=FilePage(source=s, title=page.title(with_ns=True)),
                         source_url=page.get_file_url(),
                         comment="批量从萌娘百科搬运图片",
                         text="批量从萌娘百科搬运图片",
                         report_success=True,
                         ignore_warnings=False)
            except Exception as e:
                print(page.title(with_ns=True))
                print(e)

    workers = []
    for _ in range(1):
        t = Thread(target=upload_worker)
        t.start()
        workers.append(t)
    for w in workers:
        w.join()


def upload_files_from_commons(exclude: set):
    cont = Path("data/download_images_page_list_cont.txt")
    if not cont.exists():
        start = '!'
    else:
        start = open(cont, "r").read()
    print("Continue from", start)
    s: APISite = icu_cm()
    pages_gen = s.allpages(namespace=6, start=start)
    pages_gen = (p for p in pages_gen if p.title(with_ns=True) not in exclude and should_download(p.title()))
    page_list = []
    for p in pages_gen:
        page_list.append(p)
        if len(page_list) == 500:
            process_batch(page_list)
            page_list = []
            with open(cont, "w") as f:
                p: FilePage
                f.write(p.title(underscore=True))
    process_batch(page_list)
    cont.unlink(missing_ok=True)


# def get_mirror_file_list() -> set:
#     s = mirror()
#     pages_gen = s.allpages(namespace=6, start="!")
#     page_list = set()
#     for p in pages_gen:
#         p: Page
#         page_list.add(p.title(underscore=True))
#     return page_list

def get_mirror_file_list() -> set:
    pages_gen = QueryGenerator(site=mirror(), list='allpages', apfrom='!', aplimit=500, apnamespace=6)
    page_list = set()
    for p in pages_gen:
        page_list.add(p['title'])
    return page_list


def mirror_image_sync():
    mirror_file_list = Path("data/mirror_image_sync_mirror_image_list.pickle")
    if not mirror_file_list.exists():
        pickle.dump(get_mirror_file_list(), open(mirror_file_list, "wb"))
    existing_files = pickle.load(open(mirror_file_list, "rb"))
    upload_files_from_commons(existing_files)
    mirror_file_list.unlink()


# See PyCharm help at https://www.jetbrains.com/help/pycharm/
if __name__ == "__main__":
    mirror_image_sync()
