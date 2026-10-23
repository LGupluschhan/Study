#!/usr/bin/env python3
"""content.json → 도식이 들어간 단일 HTML 학습 노트 페이지(Artifact 게시용).

사용법: python3 build_page.py content.json out.html

- 스타일은 templates/base.css를 그대로 넣는다(라이트/다크, 모바일 거터 포함).
- 블록과 도식 스키마는 references/blocks.md 참고.
- HTML 필드(html, lead 등)는 그대로 삽입된다(<strong>, <br> 사용 가능, &는 &amp;).
  도식 라벨은 자동 이스케이프된다.
"""
import html
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CSS = (ROOT / "templates" / "base.css").read_text(encoding="utf-8")
FONTS = ("https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+KR:wght@400;500;700"
         "&family=JetBrains+Mono:wght@400;600&display=swap")
MARKERS = """<svg width="0" height="0" style="position:absolute" aria-hidden="true">
  <defs>
    <marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path class="ah" d="M0 0L10 5L0 10z"/></marker>
    <marker id="ar-a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path class="ah-a" d="M0 0L10 5L0 10z"/></marker>
    <marker id="ar-w" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path class="ah-w" d="M0 0L10 5L0 10z"/></marker>
  </defs>
</svg>"""

NODE_CLS = {"n": "n", "a": "n-a", "w": "n-w", "o": "n-o", "dash": "n-dash"}


def esc(s):
    return html.escape(str(s), quote=True)


def tw(s, size=12):
    """텍스트 폭 추정: 한글·CJK는 1em, 그 외 0.6em."""
    return sum(size if ord(c) > 0x1100 else size * 0.6 for c in str(s))


def as_node(v):
    return v if isinstance(v, dict) else {"label": v}


# ---------- SVG 기본 요소 ----------

def rect(x, y, w, h, kind="n", rx=6):
    return (f'<rect class="{NODE_CLS.get(kind, "n")}" x="{x:.0f}" y="{y:.0f}" '
            f'width="{w:.0f}" height="{h:.0f}" rx="{rx}"/>')


def text(x, y, s, cls="t", anchor="middle"):
    a = "" if anchor == "start" else f' text-anchor="{anchor}"'
    return f'<text class="{cls}" x="{x:.0f}" y="{y:.0f}"{a}>{esc(s)}</text>'


def edge(d, tone="", dash=False):
    cls = "e" + (f"-{tone}" if tone else "") + (" e-dash" if dash else "")
    mk = "ar" + (f"-{tone}" if tone else "")
    return f'<path class="{cls}" d="{d}" marker-end="url(#{mk})"/>'


def labeled_box(x, y, w, h, nd):
    out = [rect(x, y, w, h, nd.get("kind", "n"))]
    cx = x + w / 2
    if nd.get("sub"):
        out += [text(cx, y + h / 2 - 8, nd["label"]), text(cx, y + h / 2 + 8, nd["sub"], "ts")]
    else:
        out.append(text(cx, y + h / 2, nd["label"]))
    return out


def node_w(nd):
    if nd.get("kind") == "gate":
        return 2 * max(14, tw(nd["label"]) / 2 + 12)
    return max(40, tw(nd["label"]) + 18, tw(nd.get("sub", ""), 11) + 18)


def node_h(nodes):
    return 38 if any(n.get("sub") for n in nodes) else 28


def draw_node(x, cy, nd, H):
    w = node_w(nd)
    if nd.get("kind") == "gate":
        hh = H / 2 + 4
        cx = x + w / 2
        return w, [f'<path class="n-o" d="M{cx:.0f} {cy - hh:.0f} L{x + w:.0f} {cy:.0f} '
                   f'L{cx:.0f} {cy + hh:.0f} L{x:.0f} {cy:.0f} Z"/>', text(cx, cy, nd["label"])]
    return w, labeled_box(x, cy - H / 2, w, H, nd)


def row(items, x, cy, H, gap=18):
    """노드를 가로로 잇고 화살표로 연결. (parts, spans, 오른쪽 끝 x)."""
    parts, spans = [], []
    for i, nd in enumerate(items):
        if i:
            parts.append(edge(f"M{spans[-1][1]:.0f} {cy:.0f} H{x - 4:.0f}", nd.get("edge", ""), nd.get("dash", False)))
        w, p = draw_node(x, cy, nd, H)
        parts += p
        spans.append((x, x + w))
        x += w + gap
    return parts, spans, (x - gap if items else x)


def below_notes(nodes, spans, cy, H, parts):
    """노드의 note를 아래에 표시. fail=true면 주황 화살표로 '빠지는 길'을 그린다. 아래쪽 끝 y 반환."""
    bottom = cy + H / 2
    for nd, (l, r) in zip(nodes, spans):
        if not nd.get("note"):
            continue
        cx = (l + r) / 2
        top = cy + H / 2 + (4 if nd.get("kind") == "gate" else 0)
        if nd.get("fail"):
            parts.append(edge(f"M{cx:.0f} {top:.0f} V{top + 22:.0f}", "w"))
            parts.append(text(cx, top + 36, nd["note"], "ts"))
            bottom = max(bottom, top + 46)
        else:
            parts.append(text(cx, top + 14, nd["note"], "tm"))
            bottom = max(bottom, top + 24)
    return bottom


def svg(w, h, parts, s, wide=False):
    aria = esc(s.get("aria", ""))
    body = "\n".join(parts)
    if wide:
        return (f'<div class="scroll"><svg class="d" viewBox="0 0 {w:.0f} {h:.0f}" role="img" '
                f'aria-label="{aria}">\n{body}\n</svg></div>')
    return (f'<svg class="m" viewBox="0 0 {w:.0f} {h:.0f}" style="max-width:{w * 1.3:.0f}px" '
            f'role="img" aria-label="{aria}">\n{body}\n</svg>')


# ---------- 도식 생성기 ----------

def d_chain(s):
    nodes = [as_node(n) for n in s["nodes"]]
    H = node_h(nodes)
    cy = 30 + H / 2
    parts, spans, right = row(nodes, 6, cy, H)
    bottom = below_notes(nodes, spans, cy, H, parts)
    if s.get("caption"):
        parts.append(text((6 + right) / 2, 12, s["caption"], "tm"))
    return svg(right + 6, bottom + 10, parts, s, s.get("wide", False))


def d_fanout(s):
    head = [as_node(n) for n in s["head"]]
    branches = [as_node(n) for n in s["branches"]]
    tail = [as_node(n) for n in s.get("tail", [])]
    H = node_h(head + branches + tail)
    gy, top, n = H + 14, 10, len(branches)
    cy = top + (n - 1) * gy / 2 + H / 2
    parts, hspans, x = row(head, 6, cy, H)
    bx, bw = x + 34, max(node_w(b) for b in branches)
    for i, b in enumerate(branches):
        by = top + i * gy + H / 2
        xm = (x + bx) / 2
        parts.append(edge(f"M{x:.0f} {cy:.0f} C{xm:.0f} {cy:.0f} {xm:.0f} {by:.0f} {bx - 4:.0f} {by:.0f}",
                          b.get("edge", ""), b.get("dash", False)))
        parts += labeled_box(bx, by - H / 2, bw, H, b)
        if b.get("edge_label"):
            parts.append(text(xm - 4, by + (10 if by > cy else -10), b["edge_label"], "tw" if b.get("edge") == "w" else "ts", "end"))
    right = bx + bw
    tspans = []
    if tail:
        tx = right + 34
        xm = (right + tx) / 2
        for i, b in enumerate(branches):
            by = top + i * gy + H / 2
            parts.append(edge(f"M{right:.0f} {by:.0f} C{xm:.0f} {by:.0f} {xm:.0f} {cy:.0f} {tx - 4:.0f} {cy:.0f}",
                              "", b.get("dash", False)))
        p, tspans, right = row(tail, tx, cy, H)
        parts += p
    bottom = max(top * 2 + (n - 1) * gy + H,
                 below_notes(head + tail, hspans + tspans, cy, H, parts) + 10)
    return svg(right + 6, bottom, parts, s, s.get("wide", False))


def d_cycle(s):
    a, b = as_node(s["a"]), as_node(s["b"])
    H, y, ax = 40, 30, 16
    aw, bw = max(96, node_w(a)), max(96, node_w(b))
    gap = max(70, tw(s.get("forward", ""), 11) + 20, tw(s.get("back", "")) + 20)
    bx = ax + aw + gap
    mid = (ax + aw + bx) / 2
    parts = labeled_box(ax, y, aw, H, a) + labeled_box(bx, y, bw, H, b)
    parts += [edge(f"M{ax + aw:.0f} {y + 10} H{bx - 4:.0f}"), text(mid, y - 4, s.get("forward", ""), "ts"),
              edge(f"M{bx:.0f} {y + 30} H{ax + aw + 4:.0f}", "w"), text(mid, y + 52, s.get("back", ""), "tw")]
    width, h = bx + bw + 16, y + H + 30
    if s.get("exit"):
        cx = bx + bw / 2
        parts += [edge(f"M{cx:.0f} {y + H} V{y + H + 30}"), text(cx, y + H + 46, s["exit"], "ts")]
        width, h = max(width, cx + tw(s["exit"], 11) / 2 + 6), y + H + 60
    return svg(width, h, parts, s)


def d_stages(s):
    st, W, G, X0 = s["stages"], 200, 40, 20
    n = len(st)
    parts = []
    for i, g in enumerate(st):
        x = X0 + i * (W + G)
        parts += [rect(x, 20, W, 104, g.get("kind", "n"), 8),
                  text(x + 16, 40, g.get("tag", f"STAGE {i + 1}"), "tm", "start"),
                  text(x + 16, 62, g["title"], "tb", "start")]
        parts += [text(x + 16, 86 + 20 * j, ln, "ts", "start") for j, ln in enumerate(g.get("lines", [])[:2])]
        if i:
            parts.append(edge(f"M{x - G} 72 H{x - 4}"))
    width, h = X0 * 2 + n * W + (n - 1) * G, 140
    fb = s.get("feedback")
    if fb:
        to = min(fb.get("to", 1), n - 2)
        cx = X0 + to * (W + G) + W / 2
        bl, br = cx - 102, cx + 102
        lx = X0 + (n - 1) * (W + G) + W / 2
        parts += [f'<path class="e-w" d="M{lx:.0f} 124 V214 H{br + 2:.0f}"/>',
                  rect(bl, 186, 204, 56, "w", 8),
                  text(bl + 16, 202, fb.get("tag", f"STAGE {n + 1}"), "tm", "start"),
                  text(bl + 16, 224, fb["title"], "tb", "start"),
                  edge(f"M{cx:.0f} 186 V128", "w")]
        if fb.get("label"):
            parts.append(text(cx + 12, 156, fb["label"], "tw", "start"))
        if fb.get("note"):
            parts.append(text(cx, 262, fb["note"], "ts"))
        h = 280
    return svg(width, h, parts, s, wide=True)


def d_ladder(s):
    steps, X0, W, G = s["steps"], 60, 200, 10
    n = len(steps)
    tops = [150 - i * (100 / max(n - 1, 1)) for i in range(n)]
    parts = [edge("M30 220 V24", "w")]
    if s.get("axis"):
        parts.append(text(40, 22, s["axis"], "tw", "start"))
    for i, st in enumerate(steps):
        x, t = X0 + i * (W + G), tops[i]
        parts += [rect(x, t, W, 224 - t, st.get("kind", "n"), 6), text(x + 16, t + 22, st["title"], "tb", "start")]
        parts += [text(x + 16, t + 44 + 18 * j, ln, "ts", "start") for j, ln in enumerate(st.get("lines", [])[:2])]
        if i and s.get("climb"):
            px, sy, ey = X0 + (i - 1) * (W + G) + 100, tops[i - 1] - 10, t - 4
            parts += [edge(f"M{px:.0f} {sy:.0f} C{px:.0f} {sy - 30:.0f} {px + 40:.0f} {ey:.0f} {x - 8:.0f} {ey:.0f}", "", True),
                      text(px - 10, ey, s["climb"], "ts", "end")]
    return svg(X0 + n * W + (n - 1) * G + 20, 240, parts, s, wide=True)


def d_agent(s):
    ag, env = as_node(s["agent"]), as_node(s["env"])
    parts = [rect(20, 66, 120, 48, "n", 8), text(80, 90, s.get("actor", "사람 · 목표"), "tb"),
             edge("M140 90 H266"), text(203, 78, s.get("ask", "작업 지시"), "ts"),
             rect(270, 56, 170, 68, "w", 8), text(355, 82, ag["label"], "tb"), text(355, 104, ag.get("sub", ""), "ts"),
             edge("M320 56 C320 14 390 14 390 52", "w"), text(355, 14, s.get("repeat", "반복"), "tw"),
             rect(560, 56, 140, 68, "n", 8), text(630, 82, env["label"], "tb"), text(630, 104, env.get("sub", ""), "ts"),
             edge("M440 76 H556", "a"), text(498, 64, s.get("act", "행동"), "ta"),
             edge("M560 106 H444"), text(500, 142, s.get("feedback", "피드백"), "ts")]
    if s.get("stop"):
        parts += [edge("M355 124 V168"), rect(215, 172, 280, 44, "o", 8), text(355, 194, s["stop"])]
    return svg(720, 230, parts, s, wide=True)


def d_hub(s):
    ch, CW, G, X0 = s["children"], 100, 10, 10
    n = len(ch)
    width = X0 * 2 + n * CW + (n - 1) * G
    lead = s["lead"]
    lw = max(120, tw(lead["title"], 14) + 24)
    lx = width / 2 - lw / 2
    parts = [rect(lx, 12, lw, 44, lead.get("kind", "w"), 8), text(width / 2, 28, lead["title"], "tb"),
             text(width / 2, 45, lead.get("sub", ""), "ts")]
    for i, c in enumerate(ch):
        x = X0 + i * (CW + G)
        cx, sx = x + CW / 2, lx + lw * (i + 1) / (n + 1)
        parts += [edge(f"M{sx:.0f} 56 C{sx:.0f} 90 {cx:.0f} 90 {cx:.0f} 126", "", c.get("dash", False)),
                  rect(x, 130, CW, 62, c.get("kind", "a"), 8), text(cx, 148, c["title"])]
        parts += [text(cx, 166 + 16 * j, ln, "ts") for j, ln in enumerate(c.get("lines", [])[:2])]
    if s.get("edge_label"):
        parts.append(text(width / 2 + 8, 96, s["edge_label"], "tm", "start"))
    return svg(width, 210, parts, s)


def d_peers(s):
    (g1, g2) = s["groups"][:2]
    parts = [f'<rect class="bound" x="8" y="20" width="136" height="176" rx="10"/>', text(20, 36, g1["boundary"], "tm", "start"),
             f'<rect class="bound" x="196" y="20" width="136" height="176" rx="10"/>', text(208, 36, g2["boundary"], "tm", "start"),
             rect(26, 88, 100, 44, "a", 8), text(76, 110, g1["agent"]),
             rect(214, 88, 100, 44, "a", 8), text(264, 110, g2["agent"]),
             edge("M128 104 H210", "a"), edge("M212 118 H130", "a")]
    parts += [text(170, 150 + 16 * j, ln, "ta") for j, ln in enumerate(s.get("label", []))]
    return svg(340, 210, parts, s)


def d_raw(s):
    return s["svg"]


DIAGRAMS = {"chain": d_chain, "fanout": d_fanout, "cycle": d_cycle, "stages": d_stages, "ladder": d_ladder,
            "agent": d_agent, "hub": d_hub, "peers": d_peers, "raw": d_raw}


# ---------- 블록 ----------

def en(b):
    return f' <span class="en">{b["en"]}</span>' if b.get("en") else ""


def blocks(items):
    return "\n".join(BLOCKS[b["t"]](b) for b in items)


def b_fig(b):
    cap = f'<div class="fig-cap">{b["cap"]}</div>' if b.get("cap") else ""
    return f'<div class="fig">{cap}\n{blocks(b.get("items", []))}\n</div>'


def b_cards(b):
    out = []
    for c in b["items"]:
        dia = DIAGRAMS[c["diagram"]["kind"]](c["diagram"]) if c.get("diagram") else ""
        body = f'<p>{c["html"]}</p>' if c.get("html") else ""
        fit = f'<div class="fit"><b>{c["fit"]["label"]}:</b> {c["fit"]["html"]}</div>' if c.get("fit") else ""
        out.append(f'<div class="pat"><h4>{c["title"]}{en(c)}</h4>{dia}{body}{fit}</div>')
    return '<div class="patterns">\n' + "\n".join(out) + "\n</div>"


def b_backward(b):
    head = f'<div class="arrow-row"><span>{b.get("left", "")}</span><span>{b.get("right", "")}</span></div>'
    steps = "".join(f'<div class="step {s.get("role", "")}"><span class="k">{s["k"]}</span>'
                    + (f'<strong>{s["html"]}</strong>' if s.get("role") else s["html"]) + "</div>" for s in b["steps"])
    return head + f'<div class="backward">{steps}</div>'


def b_split(b):
    m, r = b["main"], b["rest"]
    bar = (f'<div class="split" role="img" aria-label="{esc(b.get("aria", ""))}">'
           f'<div class="fast" style="flex:{m.get("flex", 9)}">{m["label"]}</div>'
           f'<div class="slow" style="flex:{r.get("flex", 1.6)}">{r["label"]}</div></div>')
    leg = "".join(f"<span>{x}</span>" for x in b.get("legend", []))
    return bar + (f'<div class="legend">{leg}</div>' if leg else "")


BLOCKS = {
    "p": lambda b: f'<p class="prose">{b["html"]}</p>',
    "note": lambda b: f'<p class="note">{b["html"]}</p>',
    "h3": lambda b: f'<h3>{b["text"]}{en(b)}</h3>',
    "tasks": lambda b: '<div class="tasks">' + "".join(
        f'<div class="task"><b>{no}</b><span>{t}</span></div>' for no, t in b["items"]) + "</div>",
    "quote": lambda b: f'<p class="quote prose">{b["html"]}' + (f'<small>{b["small"]}</small>' if b.get("small") else "") + "</p>",
    "fig": b_fig,
    "diagram": lambda b: DIAGRAMS[b["kind"]](b),
    "cards": b_cards,
    "backward": b_backward,
    "spectra": lambda b: '<div class="spectra">' + "".join(
        f'<div class="spec"><span class="spec-title">{s["title"]}</span><div class="grad"></div>'
        f'<div class="ends"><span>{s["left"]}</span><span>{s["right"]}</span></div></div>' for s in b["items"]) + "</div>",
    "callout": lambda b: f'<div class="callout {"warm" if b.get("tone") == "warm" else ""}">'
                         f'<span class="eyebrow">{b["eyebrow"]}</span>\n{blocks(b.get("items", []))}\n</div>',
    "vs": lambda b: '<div class="vs">' + "".join(
        f'<div class="{v.get("tone", "accent")}"><span class="tag">{v["tag"]}</span>{v["html"]}</div>' for v in b["items"]) + "</div>",
    "chips": lambda b: '<div class="chips">' + "".join(f'<span class="chip">{c}</span>' for c in b["items"]) + "</div>",
    "pillars": lambda b: '<div class="pillars">' + "".join(
        f'<div class="pillar"><h4>{p["title"]}{en(p)}</h4><span>{p["html"]}</span>'
        + (f'<span class="ev">{p["ev"]}</span>' if p.get("ev") else "") + "</div>" for p in b["items"]) + "</div>",
    "split": b_split,
    "takeaways": lambda b: '<ul class="takeaways">' + "".join(f"<li><span>{t}</span></li>" for t in b["items"]) + "</ul>",
    "html": lambda b: b["html"],
}


# ---------- 페이지 ----------

def page(c):
    weight = ""
    if c.get("weight"):
        w = c["weight"]
        weight = (f'<div class="weight"><div class="weight-bar" role="img" aria-label="{esc(w["label"])}">'
                  f'<span style="width:{w["pct"]}%"></span></div><small>{w["label"]}</small></div>')
    secs = []
    for s in c["sections"]:
        no = f'<span class="no">{s["no"]}</span>' if s.get("no") else ""
        secs.append(f'<section>\n<h2>{no}{s["title"]}{en(s)}</h2>\n{blocks(s["blocks"])}\n</section>')
    src = c.get("source")
    source = (f'<p class="source">원문: <a href="{esc(src["url"])}">{src["label"]}</a> '
              f'{src.get("tail", "페이지 내용만 한국어로 정리하고 도식화했습니다.")}</p>') if src else ""
    return f"""<title>{esc(c["title"])}</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<style>
{CSS}</style>

{MARKERS}

<div class="wrap">

<header>
  <div class="eyebrow">{c.get("eyebrow", "")}</div>
  <h1>{c["h1"]}{f' <span class="en">{c["h1_en"]}</span>' if c.get("h1_en") else ""}</h1>
  {f'<p class="lead prose">{c["lead"]}</p>' if c.get("lead") else ""}
  {weight}
</header>

{chr(10).join(secs)}

{source}

</div>
"""


def main():
    if len(sys.argv) != 3:
        sys.exit("사용법: python3 build_page.py content.json out.html")
    content = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
    out = pathlib.Path(sys.argv[2])
    out.write_text(page(content), encoding="utf-8")
    print(f"생성: {out} ({out.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
