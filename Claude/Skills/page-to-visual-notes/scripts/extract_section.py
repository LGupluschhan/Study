#!/usr/bin/env python3
"""웹 페이지(또는 저장된 HTML)에서 id 하나에 해당하는 요소만 잘라 읽기 쉬운 텍스트 개요로 출력한다.

사용법:
  python3 -I extract_section.py <URL|파일> --list [--filter page-]   # id 목록 보기
  python3 -I extract_section.py <URL|파일> [id] [-o out.md]           # 해당 섹션만 개요로
  URL에 #anchor가 붙어 있으면 id는 생략할 수 있다.

출력 규칙: 제목은 #, 목록은 -, 표 행은 | 셀 | 형태, 굵게는 **. script/style/svg는 버린다.
"""
import argparse
import re
import sys
import urllib.parse
import urllib.request
from html.parser import HTMLParser

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
HEADINGS = {"h1", "h2", "h3", "h4", "h5", "h6"}
BLOCKS = {"p", "div", "section", "article", "blockquote", "pre", "table", "ul", "ol", "figure", "figcaption", "aside"}
SKIP = {"script", "style", "svg", "noscript"}


def load(src):
    if re.match(r"https?://", src):
        req = urllib.request.Request(src, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            charset = r.headers.get_content_charset() or "utf-8"
            return r.read().decode(charset, errors="replace")
    with open(src, encoding="utf-8", errors="replace") as f:
        return f.read()


class IdLister(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"):
            self.ids.append((tag, a["id"]))


class Extract(HTMLParser):
    """target id 요소의 시작부터 짝이 맞는 닫는 태그까지 텍스트화. 닫는 태그가 생략된 HTML도 스택으로 견딘다."""

    def __init__(self, target):
        super().__init__(convert_charrefs=True)
        self.target, self.stack, self.out = target, [], []
        self.on = self.done = False
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if self.done:
            return
        if not self.on:
            if dict(attrs).get("id") != self.target:
                return
            self.on = True
        if tag in VOID:
            if tag == "br" and not self.skip:
                self.out.append("\n")
            return
        self.stack.append(tag)
        if tag in SKIP:
            self.skip += 1
        if self.skip:
            return
        if tag in HEADINGS:
            self.out.append("\n\n" + "#" * int(tag[1]) + " ")
        elif tag == "li":
            self.out.append("\n- ")
        elif tag == "tr":
            self.out.append("\n| ")
        elif tag in BLOCKS:
            self.out.append("\n")
        elif tag in ("strong", "b"):
            self.out.append("**")
        elif tag == "code":
            self.out.append("`")

    def handle_endtag(self, tag):
        if not self.on or self.done or tag in VOID or tag not in self.stack:
            return
        while self.stack:
            t = self.stack.pop()
            if t in SKIP:
                self.skip -= 1
            elif not self.skip:
                if t in ("td", "th"):
                    self.out.append(" | ")
                elif t in ("strong", "b"):
                    self.out.append("**")
                elif t == "code":
                    self.out.append("`")
                elif t in BLOCKS or t in HEADINGS:
                    self.out.append("\n")
            if t == tag:
                break
        if not self.stack:
            self.done = True

    def handle_data(self, data):
        if self.on and not self.done and not self.skip:
            self.out.append(re.sub(r"\s+", " ", data))

    def text(self):
        s = "".join(self.out)
        s = re.sub(r"[ \t]+\n", "\n", s)
        s = re.sub(r"\n[ \t]+", "\n", s)
        return re.sub(r"\n{3,}", "\n\n", s).strip() + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src", help="URL 또는 로컬 HTML 파일")
    ap.add_argument("id", nargs="?", help="잘라낼 요소의 id (URL의 #anchor로 대체 가능)")
    ap.add_argument("--list", action="store_true", help="id 목록만 출력")
    ap.add_argument("--filter", default="", help="--list 때 이 문자열이 든 id만")
    ap.add_argument("-o", "--out", help="결과 저장 경로 (생략 시 stdout)")
    a = ap.parse_args()

    url_part, _, frag = a.src.partition("#")
    html = load(url_part)

    if a.list:
        p = IdLister()
        p.feed(html)
        for tag, i in p.ids:
            if a.filter in i:
                print(f"{tag}#{i}")
        return

    target = a.id or urllib.parse.unquote(frag)
    if not target:
        sys.exit("id를 지정하거나 URL에 #anchor를 붙이세요. (--list로 목록 확인)")
    p = Extract(target)
    p.feed(html)
    if not p.on:
        sys.exit(f"id='{target}' 요소를 찾지 못했습니다. --list로 확인하세요.")
    txt = p.text()
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(txt)
        print(f"저장: {a.out} ({len(txt)}자)")
    else:
        sys.stdout.write(txt)


if __name__ == "__main__":
    main()
