"""뉴스 JSON을 정적 HTML로 만든다. JS 없이도 기사가 보인다.

사용: python build.py <news.json> <output.html>
"""
import json
import sys
from html import escape
from pathlib import Path
from urllib.parse import urlparse

TEMPLATE = Path(__file__).resolve().parent.parent / "assets" / "template.html"

ALLOWED = {
    "economist.com", "nytimes.com", "wsj.com", "ft.com", "washingtonpost.com",
    "bloomberg.com", "reuters.com", "apnews.com", "theguardian.com", "bbc.com",
    "bbc.co.uk", "theatlantic.com", "newyorker.com", "nature.com", "science.org",
    "technologyreview.com", "wired.com",
}

BADGES = {
    "The Economist": ("E", "#e3120b"), "The New York Times": ("NYT", "#121212"),
    "The Wall Street Journal": ("WSJ", "#0274b6"), "Financial Times": ("FT", "#d9a585"),
    "The Washington Post": ("WP", "#2a2a2a"), "Bloomberg": ("B", "#5c2fe5"),
    "Reuters": ("R", "#fa6400"), "Associated Press": ("AP", "#e81d25"),
    "The Guardian": ("G", "#052962"), "BBC News": ("BBC", "#bb1919"),
    "The Atlantic": ("A", "#1a1a1a"), "The New Yorker": ("NY", "#a8241f"),
    "Nature": ("N", "#008b47"), "Science": ("S", "#b31b1b"),
    "MIT Technology Review": ("TR", "#ff4f4f"), "Wired": ("W", "#111111"),
}


def host(url):
    h = urlparse(url).hostname or ""
    return h[4:] if h.startswith("www.") else h


def check(items):
    errors = []
    urls = [it["url"] for it in items]
    if len(set(urls)) != len(urls):
        errors.append("중복 URL이 있습니다.")
    for it in items:
        h = host(it["url"])
        if not any(h == d or h.endswith("." + d) for d in ALLOWED):
            errors.append(f"허용 목록 밖 도메인: {it['url']}")
    return errors


def card(it):
    e = lambda k: escape(str(it.get(k, "") or ""))
    initials, color = BADGES.get(it.get("outlet"), ((it.get("outlet") or "?")[:1], "#8e8e93"))
    sub = " · ".join(x for x in (e("category"), e("publishedAt")) if x)
    title_en = f'\n      <p class="title-en">{e("title")}</p>' if it.get("titleKo") else ""
    why = (f'\n      <p class="why"><b>왜 중요한가</b>{e("whyItMatters")}</p>'
           if it.get("whyItMatters") else "")
    verified = f" · 확인: {e('verifiedBy')}" if it.get("verifiedBy") else ""
    return f'''    <a class="card glass" href="{e("url")}" target="_blank" rel="noopener noreferrer" data-category="{e("category")}">
      <div class="meta">
        <div class="badge" style="background:{color}">{escape(initials)}</div>
        <div class="meta-text"><div class="outlet">{e("outlet")}</div><div class="sub">{sub}</div></div>
        <div class="rank">{int(it.get("rank", 0)):02d}</div>
      </div>
      <h2 class="title-ko">{e("titleKo") or e("title")}</h2>{title_en}
      <p class="summary">{e("summary")}</p>{why}
      <div class="foot"><span>{escape(host(it["url"]))}{verified}</span><span class="open">기사 열기 ›</span></div>
    </a>'''


def build(data):
    items = sorted(data.get("items", []), key=lambda it: it.get("rank", 0))
    cats = ["전체"] + list(dict.fromkeys(it["category"] for it in items if it.get("category")))
    chips = "".join(
        f'<button type="button" class="chip{" on" if c == "전체" else ""}" data-category="{escape(c)}">{escape(c)}</button>'
        for c in cats)
    note = data.get("note")
    outlets = list(dict.fromkeys(it.get("outlet", "") for it in items))
    footer = (f"<div>출처: {escape(', '.join(outlets))}</div>"
              f"<div>생성: {escape(data.get('generatedAt', ''))} · 요약은 원문을 바탕으로 작성되었습니다.</div>")
    html = TEMPLATE.read_text(encoding="utf-8")
    for key, val in {
        "{{TITLE}}": escape(f"AI 뉴스 · {data.get('date', '')}"),
        "{{SUBTITLE}}": escape(f"{data.get('dateLabel') or data.get('date', '')} · {len(items)}개 기사"),
        "{{CHIPS}}": chips,
        "{{NOTICE}}": f'<div class="notice glass">{escape(note)}</div>' if note else "",
        "{{CARDS}}": "\n".join(card(it) for it in items),
        "{{FOOTER}}": footer,
    }.items():
        html = html.replace(key, val)
    return html, items


def main():
    if len(sys.argv) != 3:
        sys.exit("사용: python build.py <news.json> <output.html>")
    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    html, items = build(data)
    errors = check(items)
    if errors:
        sys.exit("검증 실패:\n" + "\n".join(errors))
    Path(sys.argv[2]).write_text(html, encoding="utf-8")
    print(f"저장: {sys.argv[2]} (기사 {len(items)}개)")


if __name__ == "__main__":
    main()
