---
slug: patent-novelty-skill
name: patent-novelty-skill
displayName: 专利查新与创新性评价
version: 1.0.0
description: |
  封装"国知局(PSS/公布站) + WOS + CNKI + WebSearch"四位一体专利查新与新颖性 / FTO / 创新性评价工作流。
  当用户要求做专利查新、专利思路梳理、新颖性 / 创造性 / 创新性评价、FTO 规避分析、找"还没人用过的技术体系"时调用。
  遇 CNKI / 国知局 PSS / SmartLib 等需要登录或验证时，自动弹出真实浏览器登录窗口（tools/open_login.py），绝不静默跳过或假装零结果。
author: 老吴
agent_created: true
user-invocable: true
---

# 专利查新与创新性评价

把本次"通过 PSS、WOS、CNKI 检索 → 交叉验证 → 新颖性 / FTO / 创新性评价"的完整流程固化成可复用技能。
下次用户说"帮我做个专利查新""评价一下这个方案的创新性""找找哪些技术体系还没人用在 XX 上""做 FTO 规避分析"，就调用本技能。

## 适用触发

- "专利查新 / 查新检索 / 做 FTO"
- "评价这个专利思路的创新性 / 新颖性 / 创造性"
- "找 XXX 领域还没被用过的催化剂 / 材料 / 工艺"
- "这个方案能不能写进独权 / 会不会侵权"
- 配套 `patent-disclosure-skill`：本技能只做"查"和"评"，不写交底书正文。

## 核心原则（红线）

1. **交叉验证**：任何一条"已有 prior-art"结论，必须至少附一个可核验来源（专利号 / DOI / 稳定 URL），禁止凭空断言"已有人做过"。
2. **登录不静默**：检测到需登录 / 验证（见下方信号）时，立即调 `tools/open_login.py` 弹出真实浏览器登录窗口，并在对话中提示用户完成登录后再继续；**不得**用"查不到 = 不存在"蒙混。
3. **已用 vs 空白**：评价结论必须明确区分"该体系已被用于该目的（须规避）"与"该体系尚未被用于该目的（可写入 / 可主张）"。
4. **不臆造**：检索不到 ≠ 不存在。WAF / 验证码 / 配额耗尽 / 网络错误都属于"检索失败"，必须在报告里注明，不得写成"零结果"。

## 执行流程（四阶段）

### 阶段 0 · 受理（Intake）

向用户确认或自行拆解：
- 技术领域与要评价的核心技术方案（材料 / 工艺 / 系统 / 用途）。
- 候选权利要求要点（用户若已给独立权利要求，直接据此拆特征）。
- 地域范围（中国 / 全球；默认至少覆盖 CN + WOS）。
- 输出粒度（简版清单 / 完整 FTO 报告）。

若信息过粗，至多追问 **1 次**关键项（技术目的 + 核心材料），不要连环发问。

### 阶段 1 · 拆分检索主题

把方案拆成若干"技术特征 → 检索式"映射：
- 每个特征给出：① 中英文关键词集合；② 候选 IPC 分类号（先广后窄）。
- 例：目的="亚氯酸盐→ClO₂"、手段="光催化 ZnO/BiOCl" → 关键词 {chlorite, chlorine dioxide, photocataly*, ZnO, BiOCl} + IPC {C01B11/02, C02F1/30, B01J23/06}。

### 阶段 2 · 四位一体检索

按 `references/sources.md` 的逐源命令执行；四源互补，至少跑满"国知局 + WOS + CNKI + WebSearch 交叉验证"。

1. **国知局（CNIPA）两段式**
   - 第 1 段：关键词（名称 / 摘要）初检，发现相关专利与其实际 IPC。
   - 第 2 段：用初检得到的 IPC 做 `--class` 聚焦检索（见 `references/sources.md`）。
   - 工具：`patent-disclosure-skill/skills/patent-search/tools/cnipa_search.py`（需系统 Python 3.14 + playwright；未安装该依赖或不可用则降级 WebSearch `site:patents.google.com`）。可用环境变量 `CNIPA_SEARCH_TOOL` 覆盖工具路径。
2. **WOS / 外文**：WebSearch 主题词 + 关键 DOI / 出版社页 + Google Scholar；专利先验优先 Google Patents。
3. **CNKI（中文论文）**：优先 `global-biblio-base` 技能的 `/search/cn`（CNKI 索引）；无额度则 WebSearch 知网。
4. **WebSearch 交叉验证**：对每条关键 prior-art 做二次核验（确认论文 / 专利真实存在、拿到 DOI 或专利号）。

### 阶段 3 · 新颖性 / FTO / 创新性评价

按 `prompts/novelty_eval.md` 的框架产出：
- **已用体系清单（须规避）**：该技术手段已被用于相同 / 相似目的者，列出来源与规避要点。
- **空白体系清单（可写入）**：尚未被如此使用者，作为可主张创新点。
- **新颖性 / 创造性结论**：相对最接近现有技术，方案是否被公开（新颖性）、是否显而易见（创造性）。
- **独权窄化策略**：给出为避开 prior-art 而应收窄的独立权利要求表述建议。
- **FTO 风险**：是否落入他人有效专利权、是否需自由实施声明或回避设计。

### 阶段 4 · 交付

- 默认产出 Markdown 报告，落到工作区 `outputs/patent-novelty/{案件名}_{YYYYMMDDHHMMSS}.md`。
- 报告含：检索式与来源、已用 / 空白清单、评价结论、独权建议、局限性声明（哪些源未跑全 / 登录未完成）。
- 中文摘要先讲结论，再给证据。

## 登录窗口机制（重点）

**触发信号**（命中任一即视为"需要登录 / 验证"）：
- HTTP 403 / 401 且页面含"请登录""登录后可查看""账号登录"。
- 页面出现"验证码""滑块验证""行为验证""人机校验"。
- 国知局 PSS（pss-system.cponline.cnipa.gov.cn）跳登录页。
- SmartLib 返回 429（免费额度耗尽，需充值 → 也弹窗）。
- CNKI kns 直接访问被拦截要求登录。

**动作**：
```bash
python tools/open_login.py --url "<登录/验证页 URL>" --title "CNKI 登录" --message "请完成登录后回到对话说'已登录'"
```
- 该脚本用系统默认浏览器弹出**真实登录窗口**；同时在 stdout 打印提示供你转述给用户。
- 弹窗后**暂停**当前检索分支，待用户回复"已登录"再继续（不要静默改用空结果）。
- 若 SmartLib 429：弹充值页（同 `open_login.py --url <pay页>`）并提示用户，或转 WebSearch 兜底（明确告知额度耗尽）。

## 依赖

- 国知局自动爬取：`/c/Python314/python.exe` + `pip install playwright pyyaml`（Chromium 已缓存在本机）。
- CNKI / SmartLib：`global-biblio-base` 技能（网关配置已在其 `config.json`）。
- 登录窗口：`tools/open_login.py` 仅用标准库 `webbrowser`，无需额外安装；可选 `--headed` 走 Playwright 有头浏览器。
- 详见 `tools/requirements.txt`。
