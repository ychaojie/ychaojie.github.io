#!/usr/bin/env python3
"""把《高性价比人生指南》(eternity4719/HowToLiveBetter) 的 book/*.md
重排成静态阅读页。

用法：
    python tools/build-guide.py [源仓库目录]

源仓库目录缺省为临时克隆路径；也可传入任意本地 clone 的根目录。
"""

import re
import sys
from pathlib import Path

import markdown


HERE = Path(__file__).resolve().parent
OUT = HERE.parent  # life-guide/
DEFAULT_SRC = Path.home() / "AppData/Local/Temp/HowToLiveBetter"
SYNC_DATE = "2026-10-17"
REPO_URL = "https://github.com/eternity4719/HowToLiveBetter"
LICENSE_URL = "https://creativecommons.org/licenses/by/4.0/"


GROUPS = [
    ("健康与长寿", [1, 2, 16, 17, 24, 28, 33, 34]),
    ("应急与安全", [13, 14, 29]),
    ("金钱与消费", [5, 6, 7, 15, 25]),
    ("法律红线与防骗", [8, 9, 11]),
    ("工作、创业与技能", [12, 19, 23, 26, 31]),
    ("婚恋、生育与育儿", [10, 18, 20, 27, 30]),
    ("出国、旅行与留学", [21, 32]),
    ("精力、时间与放松", [3, 4, 22]),
]

RESOURCES = [
    ("寿命", "活得更久，少死于本来可以避免的事。"),
    ("时间与精力", "活着的时间不花在没有回报的事上，注意力少被白耗。"),
    ("金钱", "少花冤枉钱，把钱花在收益确定的地方。"),
    ("人身自由", "不因为不知道一条红线，把自己送进拘留所或看守所。"),
]

FIELD_LABELS = {
    "成本": "成本",
    "说人话": "说人话",
    "收益": "收益",
    "来源": "来源",
    "备注": "备注",
}


def wrap_urls(s: str) -> str:
    """给裸 URL 补上尖括号，交给 markdown 的 autolink 渲染。"""
    protected = []

    def protect(m):
        protected.append(m.group(0))
        return "\u0000%d\u0000" % (len(protected) - 1)

    s = re.sub(r"\[[^\]]*\]\([^)]+\)", protect, s)
    s = re.sub(r"<https?://[^>]+>", protect, s)

    def one(m):
        u = m.group(0)
        while u and u[-1] in "；。，、）】』」〉》！？；：":
            u = u[:-1]
        return "<%s>" % u

    s = re.sub(r"(https?://[^\s<>\"']+)", one, s)
    for i, p in enumerate(protected):
        s = s.replace("\u0000%d\u0000" % i, p)
    return s


def md_inline(s: str) -> str:
    html = markdown.markdown(wrap_urls(s))
    html = re.sub(r"^<p>(.*)</p>$", r"\1", html, flags=re.S)
    return html.strip()


def md_block(s: str) -> str:
    return markdown.markdown(wrap_urls(s)).strip()


def plain_text(s: str) -> str:
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"[*_`#]", "", s)
    return s.strip()


def parse_chapter(text: str):
    lines = text.splitlines()
    if lines and lines[0].startswith("[←"):
        lines = lines[1:]

    title = ""
    start = 0
    for i, ln in enumerate(lines):
        if ln.startswith("# "):
            title = ln[2:].strip()
            start = i + 1
            break

    m = re.match(r"^(\d+)\.\s*(.*)$", title)
    num = int(m.group(1)) if m else 0
    name = m.group(2) if m else title

    intro_lines = []
    items = []
    cur_item_lines = []
    for ln in lines[start:]:
        if ln.startswith("### "):
            if cur_item_lines:
                items.append(parse_item("\n".join(cur_item_lines)))
                cur_item_lines = []
            cur_item_lines = [ln[4:]]
        else:
            if cur_item_lines:
                cur_item_lines.append(ln)
            else:
                intro_lines.append(ln)
    if cur_item_lines:
        items.append(parse_item("\n".join(cur_item_lines)))

    return {"num": num, "name": name, "intro": intro_lines, "items": items}


def parse_item(block: str):
    lines = block.splitlines()
    head = lines[0]
    m = re.match(r"^(\d+)\.\s*(.*)$", head)
    no = int(m.group(1)) if m else 0
    title = m.group(2) if m else head

    fields = {}
    tags = {}
    cur = None
    for ln in lines[1:]:
        s = ln.strip()
        if s.startswith("<!--") and s.endswith("-->"):
            inner = s[4:-3].strip()
            inner = inner.split(":", 1)[-1].strip()
            for part in inner.split():
                if "=" in part:
                    k, v = part.split("=", 1)
                    tags[k] = v
            continue
        fm = re.match(
            r"^-\s*(成本|说人话|收益|证据等级|来源|备注)[：:]\s*(.*)$", ln
        )
        if fm:
            cur = fm.group(1)
            fields[cur] = fm.group(2)
        elif s == "":
            continue
        else:
            if cur:
                fields[cur] = fields.get(cur, "") + "\n" + ln
    return {"no": no, "title": title, "fields": fields, "tags": tags}


def intro_html(chapter) -> str:
    prose = []
    topics = []
    for ln in chapter["intro"]:
        s = ln.strip()
        if not s:
            continue
        tm = re.match(r"^\*\*(.+?)\*\*\s*[：:]\s*(.*)$", s)
        if tm:
            topics.append((tm.group(1), tm.group(2)))
        else:
            prose.append(s)
    out = []
    if prose:
        out.append(md_block("\n\n".join(prose)))
    if topics:
        for name, desc in topics:
            out.append(
                '<div class="topic"><span class="topic-name">%s</span>'
                '<span class="topic-desc">%s</span></div>'
                % (name, md_inline(desc))
            )
    return "\n".join(out)


def first_desc(chapter) -> str:
    for ln in chapter["intro"]:
        s = ln.strip()
        if not s:
            continue
        if re.match(r"^\*\*.+\*\*\s*[：:]", s):
            continue
        if "本节条目按主题" in s or "条号" in s:
            continue
        d = plain_text(s)
        if len(d) >= 8:
            return d[:52] + ("…" if len(d) > 52 else "")
    return ""


def chips_html(tags: dict) -> str:
    order = ["钱", "时间", "毅力", "收益", "口径", "人群"]
    out = []
    for k in order:
        if k in tags:
            v = tags[k]
            out.append('<span class="chip">%s=%s</span>' % (k, v))
    for k, v in tags.items():
        if k not in order:
            out.append('<span class="chip chip-muted">%s=%s</span>' % (k, v))
    return "\n".join(out)


def evidence_html(fields: dict) -> str:
    ev = fields.get("证据等级", "").strip()
    ev = re.sub(r"[^A-Ca-c]", "", ev)[:1].upper() or "C"
    label = {"A": "证据 A", "B": "证据 B", "C": "证据 C"}[ev]
    return '<span class="ev-badge ev-%s">%s</span>' % (ev, label)


def field_html(label: str, value: str, cls: str = "") -> str:
    return (
        '<div class="field %s">'
        '<span class="field-label">%s</span>'
        '<div class="field-body">%s</div>'
        "</div>" % (cls, label, md_inline(value))
    )


def item_card(item) -> str:
    f = item["fields"]
    head_meta = evidence_html(f) + chips_html(item["tags"])
    body = []
    if "成本" in f:
        body.append(field_html("成本", f["成本"]))
    if "说人话" in f:
        body.append(
            '<div class="says"><span class="field-label">说人话</span>'
            '<div class="field-body">%s</div></div>' % md_inline(f["说人话"])
        )
    if "收益" in f:
        body.append(field_html("收益", f["收益"]))
    if "来源" in f:
        body.append(field_html("来源", f["来源"], "field-source"))
    if "备注" in f:
        body.append(field_html("备注", f["备注"]))
    return (
        '<article class="item-card" id="t%d">'
        '<div class="item-head">'
        '<span class="item-no">%d</span>'
        '<h2 class="item-title">%s</h2>'
        '<div class="item-meta">%s</div>'
        "</div>"
        '<div class="item-body">%s</div>'
        "</article>"
        % (item["no"], item["no"], md_inline(item["title"]), head_meta, "\n".join(body))
    )


def page(title: str, body: str, home_active: bool = False) -> str:
    return (
        '<!doctype html>\n<html lang="zh-CN">\n<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '<meta name="description" content="高性价比人生指南 · 重新排版的阅读版">\n'
        "<title>%s</title>\n"
        '<link rel="icon" href="favicon.svg" type="image/svg+xml">\n'
        '<link rel="stylesheet" href="css/guide.css">\n'
        "</head>\n<body>\n"
        '<header class="site-header"><nav class="nav container">'
        '<a class="brand" href="index.html">高性价比人生指南</a>'
        '<ul class="nav-links">'
        '<li><a href="index.html#toc">目录</a></li>'
        '<li><a href="index.html#cite">引用</a></li>'
        "</ul></nav></header>\n"
        '<main class="container">%s</main>\n'
        '<footer class="site-footer"><div class="container">'
        '<p>内容整理自《高性价比人生指南》'
        '<a href="%s">eternity4719/HowToLiveBetter</a>（<a href="%s">CC BY 4.0</a>），'
        "本页面仅做排版与目录整理。同步自 %s 版本。</p>"
        '<p>© <span id="year"></span> · 原文以原仓库为准，办事、看病、打官司以当地部门、医生、律师的说法为准。</p>'
        "</div></footer>\n"
        '<script src="js/guide.js"></script>\n</body>\n</html>'
        % (
            title,
            body,
            REPO_URL,
            LICENSE_URL,
            SYNC_DATE,
        )
    )


def chapter_page(chapter) -> str:
    body = (
        '<nav class="crumbs"><a href="index.html">← 返回目录</a></nav>\n'
        '<h1 class="chapter-title">%d. %s</h1>\n'
        '<div class="chapter-intro">%s</div>\n'
        '<div class="items">%s</div>'
        % (
            chapter["num"],
            chapter["name"],
            intro_html(chapter),
            "\n".join(item_card(i) for i in chapter["items"]),
        )
    )
    title = "%d. %s · 高性价比人生指南" % (chapter["num"], chapter["name"])
    return page(title, body)


def index_page(chapters) -> str:
    by_num = {c["num"]: c for c in chapters}
    toc = []
    for gname, nums in GROUPS:
        rows = []
        for n in nums:
            c = by_num.get(n)
            if not c:
                continue
            desc = first_desc(c)
            rows.append(
                '<li><a href="%02d.html">'
                '<span class="toc-no">%02d</span>'
                '<span class="toc-title">%s</span>'
                '<span class="toc-desc">%s</span>'
                "</a></li>" % (n, n, c["name"], desc)
            )
        toc.append(
            '<section class="toc-group"><h3>%s</h3>'
            '<ul class="toc-list">%s</ul></section>' % (gname, "\n".join(rows))
        )

    resources = "\n".join(
        '<div class="resource-card"><h3>%s</h3><p>%s</p></div>' % (t, d)
        for t, d in RESOURCES
    )

    total_items = sum(len(c["items"]) for c in chapters)
    body = (
        '<div class="hero">'
        '<p class="hero-kicker">HOW TO LIVE BETTER</p>'
        '<h1 class="hero-title">高性价比人生指南</h1>'
        '<p class="hero-sub">用最少的钱、时间和精力，换回最多的寿命、金钱和人身自由。'
        "全书 %d 章、%d 条建议，每条写明花掉什么、换回什么、证据有多硬、出处在哪里。</p>"
        '<div class="hero-actions">'
        '<a class="btn btn-primary" href="#toc">开始阅读</a>'
        '<a class="btn btn-ghost" href="%s" target="_blank" rel="noopener">查看原仓库</a>'
        "</div></div>"
        % (len(chapters), total_items, REPO_URL)
    )

    cite = (
        '<section class="section"><div class="container">'
        '<div class="cite-card" id="cite">'
        "<h2>引用与出处</h2>"
        '<p>内容整理自《高性价比人生指南》，作者 eternity4719。</p>'
        '<p>原仓库：<a href="%s">%s</a></p>'
        '<p>许可证：<a href="%s">CC BY 4.0</a>（可转载、改编、商用，须署名并附链接）。</p>'
        "<p>本页面对原书做了重新排版与目录重组，建议条目文字尽量保留原文；同步自 %s 版本。</p>"
        '<p>原书另有检索页、PDF、EPUB、离线单文件和 Anki 牌组，见原仓库 README。</p>'
        "</div></div></section>" % (REPO_URL, REPO_URL, LICENSE_URL, SYNC_DATE)
    )

    resources_sec = (
        '<section class="section" style="padding-top:0">'
        '<div class="container"><div class="section-head">'
        '<h2 class="section-title">这本书想帮你多留住四样东西</h2></div>'
        '<div class="resource-grid">%s</div></div></section>' % resources
    )

    toc_sec = (
        '<section class="section" id="toc" style="padding-top:0">'
        '<div class="container"><div class="section-head">'
        '<h2 class="section-title">目录</h2>'
        '<p class="section-lead">34 章按主题重新分组，点击进入对应章节</p></div>'
        "%s</div></section>" % "\n".join(toc)
    )

    return page("高性价比人生指南", body + cite + resources_sec + toc_sec)


def main():
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SRC
    book = src / "book"
    if not book.is_dir():
        print("找不到源目录：%s" % src)
        sys.exit(1)

    chapters = []
    for f in sorted(book.glob("*.md")):
        chapters.append(parse_chapter(f.read_text(encoding="utf-8")))
    chapters.sort(key=lambda c: c["num"])

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "index.html").write_text(index_page(chapters), encoding="utf-8")
    for c in chapters:
        name = "%02d.html" % c["num"]
        (OUT / name).write_text(chapter_page(c), encoding="utf-8")

    print(
        "生成完成：%d 章 / %d 条 -> %s"
        % (len(chapters), sum(len(c["items"]) for c in chapters), OUT)
    )


if __name__ == "__main__":
    main()
