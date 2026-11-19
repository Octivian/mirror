#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build.py — 60天滚动窗口过滤 + 四大分类硬校验 + 生成自包含 index.html

规则：
1. 只保留近 60 天内（含当日）的情报，超过 60 天或无有效日期的自动移入 data/archive_expired.json。
2. 只保留四大动作分类：newproduct（上新类）、store（开店类）、marketing（营销类）、promo（大促类）。
3. 自动同步 feed.json 的 count 与 updated 字段，并注入 template.html 生成 index.html。
"""

import json
import pathlib
import sys
from datetime import datetime, timedelta

ROOT = pathlib.Path(__file__).resolve().parent
DATA = ROOT / "data"
WINDOW_DAYS = 60
VALID_MODULES = {"newproduct", "store", "marketing", "promo"}


def load(name: str) -> dict:
    p = DATA / name
    if not p.exists():
        sys.exit(f"[x] 缺少数据文件: {p}")
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def is_within_window(it: dict, cutoff_day: str, cutoff_month: str) -> bool:
    if it.get("module") not in VALID_MODULES:
        return False
    d = str(it.get("date") or "").strip()
    if not d:
        return False
    if len(d) >= 10:
        return d[:10] >= cutoff_day
    if len(d) == 7:
        return d >= cutoff_month
    return False


def prune_60d(feed: dict) -> tuple[dict, int]:
    today = datetime.now().date()
    cutoff = today - timedelta(days=WINDOW_DAYS)
    cutoff_day = cutoff.strftime("%Y-%m-%d")
    cutoff_month = cutoff.strftime("%Y-%m")

    kept, expired = [], []
    for it in feed.get("items", []):
        if is_within_window(it, cutoff_day, cutoff_month):
            kept.append(it)
        else:
            expired.append(it)

    if expired:
        arch_path = DATA / "archive_expired.json"
        arch = {"note": "超过 60 天或不在四大分类（上新/开店/营销/大促）的历史归档", "items": []}
        if arch_path.exists():
            try:
                arch = json.loads(arch_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        seen = {x.get("id") for x in arch.get("items", [])}
        for ex in expired:
            if ex.get("id") not in seen:
                arch.setdefault("items", []).append(ex)
                seen.add(ex.get("id"))
        arch["count"] = len(arch.get("items", []))
        arch["updated"] = datetime.now().astimezone().isoformat(timespec="seconds")
        arch_path.write_text(json.dumps(arch, ensure_ascii=False, indent=2), encoding="utf-8")

    feed["items"] = kept
    feed["count"] = len(kept)
    feed["window_days"] = WINDOW_DAYS
    feed["window_range"] = f"{cutoff_day} 至 {today.strftime('%Y-%m-%d')}"
    feed["schedule"] = "每周一 09:00 自动刷新（仅保留近 60 天：上新类 / 开店类 / 营销类 / 大促类）"
    feed["updated"] = datetime.now().astimezone().isoformat(timespec="seconds")
    (DATA / "feed.json").write_text(json.dumps(feed, ensure_ascii=False, indent=2), encoding="utf-8")
    return feed, len(expired)


def check(feed: dict, brands: dict) -> None:
    errs = []
    ids = set()
    valid_cat = set(brands.get("category_labels", {}).keys())
    valid_conf = {"high", "medium", "low"}

    for i, it in enumerate(feed.get("items", [])):
        tag = it.get("id") or f"items[{i}]"
        if not it.get("id"):
            errs.append(f"{tag}: 缺 id")
        elif it["id"] in ids:
            errs.append(f"{tag}: id 重复")
        else:
            ids.add(it["id"])

        for k in ("brand", "title", "summary", "module", "date"):
            if not it.get(k):
                errs.append(f"{tag}: 缺 {k}")

        if it.get("module") not in VALID_MODULES:
            errs.append(f"{tag}: module={it.get('module')!r} 不在 {sorted(VALID_MODULES)}")

        cat = it.get("category")
        if cat not in valid_cat:
            errs.append(f"{tag}: category={cat!r} 不在 {sorted(valid_cat)}")

        if it.get("confidence") not in valid_conf:
            errs.append(f"{tag}: confidence={it.get('confidence')!r} 非法")

    if errs:
        print("[x] 校验未通过：")
        for e in errs:
            print("    -", e)
        sys.exit(1)


def main() -> None:
    feed = load("feed.json")
    brands = load("brands.json")
    sources = load("sources.json")

    feed, expired_cnt = prune_60d(feed)
    check(feed, brands)

    payload = {
        "meta": {
            "generated": datetime.now().astimezone().isoformat(timespec="seconds"),
            "feed_updated": feed.get("updated", ""),
            "window_range": feed.get("window_range", ""),
            "window_days": WINDOW_DAYS,
            "schedule": "每周一 09:00",
            "brands_updated": brands.get("updated", ""),
            "sources_updated": sources.get("updated", ""),
        },
        "feed": feed,
        "brands": brands,
        "sources": sources,
    }

    blob = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    blob = blob.replace("</", "<\\/")

    tpl_path = ROOT / "template.html"
    tpl = tpl_path.read_text(encoding="utf-8")
    if "__DATA_PLACEHOLDER__" not in tpl:
        sys.exit("[x] template.html 里找不到 __DATA_PLACEHOLDER__")

    out = tpl.replace("__DATA_PLACEHOLDER__", blob)
    (ROOT / "index.html").write_text(out, encoding="utf-8")

    size = len(out.encode("utf-8")) / 1024
    print(f"[✓] index.html 已生成 ({size:.0f} KB) · 窗口 {feed.get('window_range')}")
    print(f"    近 60 天有效情报 {len(feed['items'])} 条（本轮自动淘汰超期/非四类 {expired_cnt} 条） / 品牌 {len(brands['brands'])} 个")


if __name__ == "__main__":
    main()
