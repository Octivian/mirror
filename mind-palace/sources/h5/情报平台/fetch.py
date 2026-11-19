#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch.py — 抓取近 60 天内「上新类 / 开店类 / 营销类 / 大促类」信源，产出 data/draft.json
"""

import json
import pathlib
import re
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timedelta

ROOT = pathlib.Path(__file__).resolve().parent
DATA = ROOT / "data"
WINDOW_DAYS = 60
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

FEEDS = [
    {
        "id": "canyin88",
        "name": "红餐网",
        "url": "https://www.canyin88.com/",
        "base": "https://www.canyin88.com",
        "pattern": r'<a[^>]+href="(/(?:zixun|zhuanlan|research|kuaixun)/[^"]+)"[^>]*>(.*?)</a>',
    },
]

CATEGORY_WORDS = [
    "蛋糕", "烘焙", "面包", "甜品", "奶油", "戚风", "可颂", "贝果", "恰巴塔",
    "吐司", "欧包", "司康", "生巧", "慕斯", "提拉米苏", "下午茶",
    "茶饮", "新茶饮", "现制茶饮", "奶茶", "果茶", "茶咖",
]

MODULE_KEYWORDS = {
    "newproduct": ["上新", "新品", "推出", "限定款", "时令", "季节限定", "菜单", "单品"],
    "store": ["首店", "开业", "新店", "开店", "入驻", "旗舰店", "快闪店", "店型", "Bistro"],
    "promo": ["双11", "双12", "店庆", "周年", "大促", "年货节", "买一送一", "买一赠一", "半价", "5折", "储值", "闪购"],
    "marketing": ["联名", "营销", "跨界", "IP", "周边", "活动", "裂变", "会员", "打卡"],
}


def classify_module(title: str) -> str:
    for mod, words in MODULE_KEYWORDS.items():
        if any(w in title for w in words):
            return mod
    return "marketing"


def fetch(url: str, retries: int = 1) -> str:
    last = None
    for i in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "zh-CN,zh;q=0.9"})
            with urllib.request.urlopen(req, timeout=15) as r:
                raw = r.read()
            for enc in ("utf-8", "gbk", "gb18030"):
                try:
                    return raw.decode(enc)
                except UnicodeDecodeError:
                    continue
            return raw.decode("utf-8", errors="ignore")
        except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
            last = e
            if i < retries:
                time.sleep(1.5)
    print(f"    [!] 抓取失败 {url}: {last}", file=sys.stderr)
    return ""


def date_from_url(href: str) -> str:
    m = re.search(r"/(\d{4})/(\d{2})/(\d{2})/", href)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    m = re.search(r"/(\d{4})(\d{2})(\d{2})/", href)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return ""


def clean(s: str) -> str:
    s = re.sub(r"<[^>]+>", "", s)
    s = s.replace("&amp;", "&").replace("&quot;", '"').replace("&nbsp;", " ").replace("&lt;", "<").replace("&gt;", ">")
    return re.sub(r"\s+", " ", s).strip()


def known_urls() -> set:
    p = DATA / "feed.json"
    if not p.exists():
        return set()
    try:
        feed = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return set()
    return {(it.get("source") or {}).get("url", "") for it in feed.get("items", [])}


def main() -> None:
    show_only = "--show" in sys.argv
    seen_urls = known_urls()
    cutoff_day = (datetime.now().date() - timedelta(days=WINDOW_DAYS)).strftime("%Y-%m-%d")
    drafts = []

    for f in FEEDS:
        print(f"[·] {f['name']}（仅保留 >= {cutoff_day}）…", end="", flush=True)
        html = fetch(f["url"])
        if not html:
            print(" 跳过")
            continue

        hits, seen = [], set()
        for href, raw_title in re.findall(f["pattern"], html, re.S):
            title = clean(raw_title)
            if len(title) < 10 or href in seen:
                continue
            seen.add(href)

            if not any(w in title for w in CATEGORY_WORDS):
                continue

            dt = date_from_url(href)
            if dt and dt < cutoff_day:
                continue

            url = f["base"] + href
            if url in seen_urls:
                continue

            mod = classify_module(title)
            hits.append({
                "title": title,
                "url": url,
                "date": dt or datetime.now().strftime("%Y-%m-%d"),
                "source": f["name"],
                "source_type": "media",
                "suggested_module": mod,
                "status": "待审",
                "review_note": "仅保留近60天【上新类/开店类/营销类/大促类】；审核后并入 feed.json",
            })

        print(f" 命中 {len(hits)} 条")
        drafts.extend(hits)

    payload = {
        "fetched_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "window_days": WINDOW_DAYS,
        "cutoff_day": cutoff_day,
        "note": "自动抓取的近 60 天草稿（已按上新/开店/营销/大促预分类）。",
        "count": len(drafts),
        "items": drafts,
    }

    if show_only:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    out = DATA / "draft.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[✓] 写入 {out.relative_to(ROOT)} · 共 {len(drafts)} 条近 60 天候选")


if __name__ == "__main__":
    main()
