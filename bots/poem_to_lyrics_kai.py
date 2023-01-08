import re
from enum import Enum
from typing import Tuple, List, Optional
from wikitextparser import parse, Template

from utils.utils import find_templates


def split(text: str, group_size: int, target_lines: Tuple) -> List[str]:
    results = [[] for _ in target_lines]
    lines = text.split("\n")
    counter = 0
    for line in lines:
        if counter == group_size:
            counter = 0
        if counter == 0 and line.strip() == "":
            for r in results:
                r.append("")
            continue
        for index, line_num in enumerate(target_lines):
            if line_num == counter:
                results[index].append(line)
                break
        counter += 1
    return ["\n".join(r) for r in results]


def remove_lj(text: str) -> str:
    parsed = parse(text)
    lj = find_templates(parsed.templates, "lj")
    for t in lj:
        t.string = t.get_arg("1").value
    cj = find_templates(parsed.templates, "cj")
    for t in cj:
        t.name = "color"
    return str(parsed)


class ColorType(Enum):
    NO_COLOR = 0,
    SINGLE_COLOR = 1,
    MULTI_COLOR = 2


def get_color(text: str) -> Tuple[ColorType, Optional[str]]:
    parsed = parse(text)
    colors = find_templates(parsed.templates, "color")
    if len(colors) == 0:
        return ColorType.NO_COLOR, None
    single_color = colors[0].get_arg("1").value.strip()
    for color in colors:
        if color.get_arg("1").value.strip() != single_color:
            return ColorType.MULTI_COLOR, None
    stack = 0
    for c in text:
        if c == '{':
            stack += 1
        elif c == '}':
            stack -= 1
        else:
            whitespace = c.isascii() and c.isspace()
            if not whitespace and stack == 0:
                return ColorType.MULTI_COLOR, single_color
    return ColorType.SINGLE_COLOR, single_color


def remove_color(text: str):
    parsed = parse(text)
    colors = find_templates(parsed.templates, "color")
    for t in colors:
        t.string = t.get_arg("2").value
    return str(parsed)


def process_multicolor(text: str) -> Tuple[str, List[str]]:
    parsed = parse(text)
    colors = find_templates(parsed.templates, "color")
    color_list = []
    for c in colors:
        color = c.get_arg("1").value
        if color not in color_list:
            color_list.append(color)
    for c in colors:
        c.string = f"@{color_list.index(c.get_arg('1').value) + 1}{c.get_arg('2').value}@"
    text = str(parsed)
    text, _ = re.subn(r'@([^\S\r\n]*@[0-9]+)', r'\1', text)
    text, _ = re.subn(r'@([^\S\r\n]*\n|$)', r'\1', text)
    return text, color_list


def split_balanced(text: str):
    sections = re.split(r"\n{2,}", text)
    chs = []
    jap = []
    for section in sections:
        lines = section.split("\n")
        assert len(lines) % 2 == 0
        line_count = len(lines) // 2
        jap.append("\n".join(lines[:line_count]))
        chs.append("\n".join(lines[line_count:]))
    return "\n\n".join(jap), "\n\n".join(chs)


def poem_to_lyrics_kai(poem: str):
    poem = poem.strip()
    # lyrics_ja, lyrics_zh = split(poem, 2, (0, 1))
    lyrics_ja, lyrics_zh = split_balanced(poem)
    lyrics_ja, lyrics_zh = lyrics_ja.strip(), lyrics_zh.strip()
    # process zh lyrics color
    color_type_zh, color_zh = get_color(lyrics_zh)
    assert color_type_zh != ColorType.MULTI_COLOR
    lyrics_zh = remove_color(lyrics_zh)
    # process ja lyrics color
    lyrics_ja = remove_lj(lyrics_ja)
    color_type_ja, color_ja = get_color(lyrics_ja)
    lyrics_kai_template = ""
    ja_colors = None
    if color_type_ja == ColorType.SINGLE_COLOR:
        lyrics_ja = remove_color(lyrics_ja)
    elif color_type_ja == ColorType.MULTI_COLOR:
        lyrics_ja, ja_colors = process_multicolor(lyrics_ja)
        lyrics_kai_template = "/colors"
    result = Template("{{LyricsKai" + lyrics_kai_template + "\n}}")
    if color_ja is not None:
        result.set_arg("lstyle", "color:" + color_ja + "\n")
    if color_zh is not None:
        result.set_arg("rstyle", "color:" + color_zh + "\n")
    if ja_colors is not None:
        result.set_arg("colors", "; ".join(ja_colors) + "\n")
    result.set_arg("original", "\n" + lyrics_ja)
    result.set_arg("translated", "\n" + lyrics_zh)
    return str(result)
