#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""通过 SmartLib 网关检索 CNKI 中文期刊文献（/search/cn）。

读取 global-biblio-base 的 config.json 获取网关地址 / 密钥 / 邮箱；
若本地未配置则提示用户提供邮箱（禁止臆造）。

流程: /consume → /search(endpoint=/search/cn, rule="K=关键词")

用法:
  python smartlib_cn_search.py "二氧化氯 催化" --page-size 20
  python smartlib_cn_search.py "光催化 亚氯酸盐 活化" --page-index 1 --email you@x.com

输出: 检索结果 JSON（标题/作者/来源/年/DOI/链接/核心标注）。
退出码: 0 成功, 1 调用失败, 2 配置缺失, 9 额度耗尽。
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path


GLOBAL_CONFIG = (
    Path(__file__).resolve().parents[2] / "global-biblio-base" / "config.json"
)


def load_cfg() -> dict:
    if GLOBAL_CONFIG.is_file():
        try:
            return json.loads(GLOBAL_CONFIG.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def post(url: str, secret: str, payload: dict):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {secret}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "ignore")
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, {"error": body[:500]}


def main() -> int:
    ap = argparse.ArgumentParser(description="SmartLib CNKI 中文期刊检索")
    ap.add_argument("query", help="检索词（拼为 K=...）")
    ap.add_argument("--page-size", type=int, default=20)
    ap.add_argument("--page-index", type=int, default=1)
    ap.add_argument("--email", default="")
    args = ap.parse_args()

    cfg = load_cfg()
    url = cfg.get("SMARTLIB_GATEWAY_URL")
    secret = cfg.get("SMARTLIB_GATEWAY_SECRET")
    email = args.email or cfg.get("SMARTLIB_EMAIL") or ""
    if not url or not secret:
        print("ERROR: 缺少网关配置，请先安装/配置 global-biblio-base", file=sys.stderr)
        return 2
    if not email:
        print(
            "ERROR: 未配置邮箱，请提供 --email 或先在 global-biblio-base/config.json 写入 SMARTLIB_EMAIL",
            file=sys.stderr,
        )
        return 2

    # 1) consume
    st, resp = post(
        f"{url}/consume",
        secret,
        {"email": email, "skill_source": "cnki-paper-search"},
    )
    if st == 429:
        print(
            "QUOTA_EXHAUSTED: SmartLib 免费额度已耗尽，请充值或改用 WebSearch。"
            "可调用 open_login.py 打开充值页。",
            file=sys.stderr,
        )
        return 9
    if st != 200 or "consume_token" not in resp:
        print(f"CONSUME_FAIL: {st} {resp}", file=sys.stderr)
        return 1
    token = resp["consume_token"]

    # 2) search
    rule = f"K={args.query}"
    body = {
        "email": email,
        "consume_token": token,
        "skill_source": "cnki-paper-search",
        "endpoint": "/search/cn",
        "rule": rule,
        "page_index": args.page_index,
        "page_size": args.page_size,
    }
    st, resp = post(f"{url}/search", secret, body)
    if st == 401:
        print(
            "TOKEN_INVALID: token 过期/已用，请重试（会自动重新 /consume）",
            file=sys.stderr,
        )
        return 1
    print(json.dumps(resp, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
