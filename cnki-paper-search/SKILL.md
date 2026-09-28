---
slug: cnki-paper-search
name: cnki-paper-search
displayName: CNKI 查论文
version: 1.0.0
description: |
  专做 CNKI（中国知网）中文学术论文检索的独立技能。主通道 SmartLib 网关 /search/cn（CNKI 索引），
  兜底 WebSearch，遇登录 / 验证墙自动弹出真实浏览器登录窗口（tools/open_login.py）。
  当用户单独说"查 CNKI 论文""找知网文献""在知网搜 XX""帮我找几篇中文期刊支撑"时调用。
author: 老吴
agent_created: true
user-invocable: true
---

# CNKI 查论文（独立技能）

只做一件事：把 CNKI 中文学术论文检索做顺、做全、可做交叉验证。
区别于 `global-biblio-base`（综合中外文献库）——本技能聚焦**知网中文论文**，流程更轻、可单独调用。

## 适用触发

- "查 CNKI 论文 / 找知网文献 / 在知网搜 XX"
- "帮我找几篇中文期刊支撑这个论点"
- "看看国内关于 XX 的研究多不多"

## 检索通道（优先级）

1. **主通道 · SmartLib `/search/cn`**（CNKI 索引，带核心收录标注、可下全文）
   - 工具：`tools/smartlib_cn_search.py`（读取 `global-biblio-base/config.json` 的网关地址/密钥/邮箱，无需重复配置）。
   - 配额：免费 100 次检索/月；耗尽（429）自动提示充值并转 WebSearch 兜底。
2. **兜底 · WebSearch 直接查知网**
   - 当 SmartLib 不可用 / 额度耗尽 / 结果不足时：
     ```bash
     WebSearch: "二氧化氯 催化 知网"
     WebSearch: "光催化 亚氯酸盐 中国期刊"
     ```
3. **登录窗口 · 直接访问 kns 被拦截时**
   - 见下方"登录窗口机制"。

## 执行流程

### 阶段 0 · 受理
确认：主题关键词、年份范围（默认近 10 年）、是否限核心/SCI、作者/机构限定、需要几条结果（默认 10–20）。
信息过粗时只追问 1 次核心关键词。

### 阶段 1 · 主通道检索
```bash
PY=/c/Python314/python.exe
CN=/c/Users/wumin/.workbuddy/skills/cnki-paper-search/tools/smartlib_cn_search.py
$PY $CN "二氧化氯 催化" --page-size 20
$PY $CN "光催化 亚氯酸盐 活化" --page-index 1
```
- 脚本自动 `/consume` → `/search/cn`，输出 JSON（标题/作者/来源/年/DOI/链接）。
- 429 → 打印 `QUOTA_EXHAUSTED`，转 WebSearch 兜底（明确告知额度耗尽）。

### 阶段 2 · 兜底与交叉验证
- WebSearch 补结果；对关键论文用 DOI / 期刊页二次核验（确认真实存在）。
- 若 WebSearch 命中"请登录 / 验证码 / 仅限机构"等拦截 → 触发登录窗口。

### 阶段 3 · 交付
默认落到 `outputs/cnki-search/{主题}_{YYYYMMDDHHMMSS}.md`，含：
- 结果表：序号 / 标题 / 作者 / 来源期刊 / 年 / 卷期 / DOI 或链接 / 核心标注 / 摘要要点。
- 检索式与覆盖源、未跑全原因（额度/登录未完成）。
- 中文摘要先讲"找到多少、最相关哪几篇"。

## 登录窗口机制（重点）

**触发信号**：HTTP 403/401 含"请登录""登录后可看"；页面出现"验证码""滑块验证"；
CNKI kns 直接访问被拦截；SmartLib 429（额度耗尽，需充值）。

**动作**：
```bash
PY=/c/Python314/python.exe
LOGIN=/c/Users/wumin/.workbuddy/skills/cnki-paper-search/tools/open_login.py
$PY $LOGIN --url "https://kns.cnki.net/kns8s/defaultresult/index" --title "CNKI 登录" --message "请完成登录后回到对话说'已登录'"
# SmartLib 额度耗尽 → 弹充值页
$PY $LOGIN --url "https://1318491188-jvmi3wist0.ap-shanghai.tencentscf.com/api/pay/alipay/create" --title "SmartLib充值"
```
- 脚本用系统默认浏览器弹出**真实登录窗口**；同时在 stdout 打印提示供你转述用户。
- 弹窗后**暂停**该检索分支，待用户说"已登录"再继续；**不得**静默改用空结果或假装零命中。
- 若仅是额度耗尽（429）且用户不想充值 → 转 WebSearch 兜底，并在交付里注明"SmartLib 额度耗尽，以下为 WebSearch 结果"。

## 依赖

- SmartLib 网关：`global-biblio-base` 技能已配置 `config.json`（URL/SECRET/EMAIL）。
- 登录窗口：`tools/open_login.py` 仅标准库 `webbrowser`，无需安装；可选 `--headed` 走 Playwright。
- 详见 `tools/requirements.txt` 与 `references/smartlib_quickref.md`。
