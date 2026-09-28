# workbuddy-patent-skills

两个面向 [WorkBuddy](https://www.workbuddy.cn) 智能体（agent）的可复用技能（skill），把"专利查新 / 创新性评价"与"CNKI 中文论文检索"流程固化下来，可在对话中通过自然语言触发词直接调用。

## 包含的技能

| 技能 | 目录 | 用途 |
|------|------|------|
| `patent-novelty-skill` | `patent-novelty-skill/` | 国知局(PSS/公布站) + WOS + CNKI + WebSearch 四位一体查新 → 新颖性 / FTO / 创新性评价 |
| `cnki-paper-search` | `cnki-paper-search/` | 专做知网(CNKI)中文学术论文检索（SmartLib 网关为主，WebSearch 兜底） |

## 安装

将本仓库的两个技能目录复制到 WorkBuddy 用户级技能目录，重开 / 刷新 WorkBuddy 即可：

```bash
cp -r patent-novelty-skill cnki-paper-search ~/.workbuddy/skills/
```

## 触发词

- **查新 / 创新性评价**："做专利查新""评价这个方案的创新性""找 XX 领域还没人用的催化剂""FTO 规避分析"
- **CNKI 查论文**："查 CNKI 论文""找知网文献""在知网搜 XX"

## 登录窗口机制（重点）

两技能在命中登录 / 验证时（HTTP 403/401 含"请登录"、验证码 / 滑块验证、国知局 PSS 登录页、SmartLib 额度耗尽 429），会调用 `tools/open_login.py` 用**系统默认浏览器弹出真实登录窗口**，并暂停该检索分支，等你登录后再继续——不会静默降级，也不会把"查不到"当成"不存在"。

```bash
python tools/open_login.py --url "https://kns.cnki.net/" --title "CNKI 登录"
```

`open_login.py` 仅用标准库 `webbrowser`，无需额外安装；可选 `--headed` 走 Playwright 有头浏览器（便于自动化抓取已登录会话）。

## 依赖

- **国知局自动爬取**（`patent-novelty-skill` 的 CNIPA 分支）：依赖 `patent-disclosure-skill` 的 `cnipa_search.py`，运行需 `python -m pip install playwright pyyaml`（Chromium 浏览器：`playwright install chromium`，或本机已装 Chrome/Edge）。未安装时自动降级为 WebSearch（`site:patents.google.com`）。可用环境变量 `CNIPA_SEARCH_TOOL` 指向该脚本的绝对路径。
- **CNKI / SmartLib**（`cnki-paper-search` 与 `patent-novelty-skill` 的 CNKI 分支）：依赖 `global-biblio-base` 技能提供网关配置（免费 100 次检索/月）；其 `tools/smartlib_cn_search.py` 会优先读取 `global-biblio-base/config.json`，缺失则向用户索取邮箱。额度耗尽时转 WebSearch 兜底。
- **登录窗口**：仅标准库，无额外依赖。

## 目录结构

```
workbuddy-patent-skills/
├── patent-novelty-skill/
│   ├── SKILL.md
│   ├── prompts/novelty_eval.md
│   ├── references/sources.md
│   └── tools/open_login.py
├── cnki-paper-search/
│   ├── SKILL.md
│   ├── prompts/cnki_search.md
│   ├── references/smartlib_quickref.md
│   └── tools/{open_login.py, smartlib_cn_search.py}
├── README.md
└── LICENSE
```

## 许可证

MIT —— 详见 [LICENSE](LICENSE)。
