#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
refresh_weekly.py — 情报平台每周一 09:00 自动刷新脚本
1. 运行 fetch.py 抓取最新公开媒体草稿（仅保留近 60 天内上新/开店/营销/大促）
2. 运行 build.py 自动剔除超过 60 天的历史旧情报（归档至 data/archive_expired.json），重新生成 index.html
3. 运行 更新宫殿.py 将最新情报台同步至 sources/h5/情报平台/index.html 与 思维宫殿.html
"""

import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent
PALACE_SCRIPT = pathlib.Path("/Users/a15608/Desktop/我的工作资料库/更新宫殿.py")


def main() -> None:
    print("=== [1/3] 抓取近 60 天候选信源 (fetch.py) ===")
    subprocess.run([sys.executable, str(ROOT / "fetch.py")], check=False)

    print("\n=== [2/3] 执行 60 天滚动窗口清理与重编译 (build.py) ===")
    subprocess.run([sys.executable, str(ROOT / "build.py")], check=True)

    if PALACE_SCRIPT.exists():
        print("\n=== [3/3] 同步至思维宫殿 H5 镜像 (更新宫殿.py) ===")
        subprocess.run([sys.executable, str(PALACE_SCRIPT)], check=True)


if __name__ == "__main__":
    main()
