#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""打开真实浏览器登录窗口，供用户在 CNKI / 国知局 PSS / SmartLib 等需要认证时登录。

用法:
  python open_login.py --url "https://login.cnki.net/..." --title "CNKI 登录"
  python open_login.py --url "https://kns.cnki.net/" --wait-sentinel "/tmp/cnki_logged_in"

行为:
  1. 用系统默认浏览器打开给定 URL（真实窗口，用户可输入账号密码 / 扫码）。
  2. 在 stdout 打印「请登录」提示，供 Agent 转述给用户。
  3. 若指定 --wait-sentinel，则轮询该文件是否出现（登录完成后由配套脚本写入），
     最多等待 --timeout 秒；否则立即返回，由 Agent 在对话中等待用户说「已登录」。
  4. 若 webbrowser 打开失败，回退为打印可复制的 URL 框与手动打开指引。

依赖: 仅标准库（webbrowser/os/sys/argparse/time/pathlib）。
可选增强: 若系统装有 playwright，可用 --headed 走 Playwright 真实有头浏览器（便于自动化抓取已登录会话）。
"""
from __future__ import annotations

import argparse
import os
import sys
import time
import webbrowser
from pathlib import Path


def open_browser(url: str) -> bool:
    try:
        return webbrowser.open(url, new=2)
    except Exception:
        return False


def open_playwright(url: str) -> bool:
    import importlib.util

    if importlib.util.find_spec("playwright") is None:
        return False
    here = Path(__file__).resolve().parent
    browser_py = (
        here.parent.parent
        / "patent-disclosure-skill"
        / "skills"
        / "patent-search"
        / "tools"
        / "browser.py"
    )
    if not browser_py.is_file():
        return False
    sys.path.insert(0, str(browser_py.parent))
    try:
        from browser import launch_chromium  # type: ignore
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser, _ = launch_chromium(p, headless=False)
            page = browser.new_page()
            page.goto(url)
            print(f"LOGIN_WINDOW: playwright opened {url}", file=sys.stderr, flush=True)
            try:
                input("登录完成后按 Enter 关闭窗口（或直接关闭浏览器）...")
            finally:
                browser.close()
        return True
    except Exception as e:  # pragma: no cover
        print(f"LOGIN_WINDOW_WARN: playwright 路径失败: {e}", file=sys.stderr, flush=True)
        return False


def main() -> int:
    ap = argparse.ArgumentParser(description="打开真实浏览器登录窗口")
    ap.add_argument("--url", required=True, help="登录页 URL")
    ap.add_argument("--title", default="登录", help="来源名称，用于提示")
    ap.add_argument("--message", default="", help="附加提示语")
    ap.add_argument("--wait-sentinel", default="", help="登录完成后由脚本写入的哨兵文件；指定则轮询")
    ap.add_argument("--timeout", type=int, default=300, help="轮询哨兵的最长等待秒数")
    ap.add_argument("--headed", action="store_true", help="尝试用 Playwright 有头浏览器（需系统装 playwright）")
    args = ap.parse_args()

    print(f"\n🔓 【{args.title}】需要登录", flush=True)
    print(f"   登录页: {args.url}", flush=True)
    if args.message:
        print(f"   说明: {args.message}", flush=True)
    print("   请在该窗口完成登录 / 验证，然后回到对话告诉我「已登录」继续。\n", flush=True)

    if args.headed and open_playwright(args.url):
        return 0

    ok = open_browser(args.url)
    if not ok:
        print("⚠️ 无法自动打开浏览器，请手动复制以下链接在浏览器打开：", flush=True)
        print(f"   {args.url}\n", flush=True)

    if args.wait_sentinel:
        sent = Path(args.wait_sentinel)
        deadline = time.time() + args.timeout
        while time.time() < deadline:
            if sent.exists():
                print("LOGIN_DONE: sentinel detected", file=sys.stderr, flush=True)
                return 0
            time.sleep(2)
        print("LOGIN_TIMEOUT: 等待登录哨兵超时", file=sys.stderr, flush=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
