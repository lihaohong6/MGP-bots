import subprocess

from utils.config import get_data_path

pre = """<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"><html><head><title></title></head><body>"""
post = "</body></html>"


def tidy_html(source: str) -> str:
    path = get_data_path().joinpath("temp.html")
    with open(path, "w") as f:
        f.write(pre + source + post)
    subprocess.run(['tidy', '-m', '--wrap', '0', '--show-body-only', '1', path])
    return open(path, 'r').read()
