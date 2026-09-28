# 逐源检索命令与策略

## 源 1 · 国知局 CNIPA（两段式）

工具：`patent-disclosure-skill/skills/patent-search/tools/cnipa_search.py`
运行器：系统 Python 3.14（已装 playwright）
```bash
PY=/c/Python314/python.exe
TOOL="${CNIPA_SEARCH_TOOL:-<patent-disclosure-skill 安装路径>/skills/patent-search/tools/cnipa_search.py}"
# 说明：国知局自动爬取依赖 patent-disclosure-skill 的 cnipa_search.py。
# 未安装该依赖时，跳过本段，改用下方 WebSearch 降级命令（site:patents.google.com）。

# 第 1 段：关键词初检（名称/摘要），发现相关专利与实际 IPC
$PY $TOOL --title "亚氯酸盐 二氧化氯" --max-pages 3
$PY $TOOL --title "chlorite chlorine dioxide photocatal" --max-pages 3

# 第 2 段：用初检得到的 IPC 聚焦检索
$PY $TOOL --class C01B11/02 --title "二氧化氯" --max-pages 5
$PY $TOOL --class C02F1/30 --title "光催化" --max-pages 5
```
- 结果落到 `outputs/patent-search/SEARCH-*.md`。
- 机读前缀：`EPUB_SEARCH_MD:`（报告路径）、`EPUB_SEARCH_JSON:`、`EPUB_SEARCH_INCOMPLETE:`（分页未全，禁止称"全部"）。
- **若 playwright 不可用** → 降级：
  ```bash
  # WebSearch 代理国知局检索
  WebSearch: "亚氯酸盐 制备 二氧化氯 专利 site:patents.google.com"
  WebSearch: "chlorite chlorine dioxide patent site:patents.google.com"
  ```
  并在报告注明"国知局自动爬取未跑（playwright 缺失），以 Google Patents + WebSearch 替代"。

## 源 2 · WOS / 外文文献与专利

```bash
# 主题检索（WebSearch）
WebSearch: "photocatalytic activation chlorite chlorine dioxide"
WebSearch: "piezocatalytic chlorite ClO2 synthesis"
# 已知 DOI / 出版社页核验
WebFetch: "https://doi.org/10.1021/acsami.2c06011"   # 核验 Su 2022 等
# Google Patents 先验
WebSearch: "chlorine dioxide preparation patent site:patents.google.com"
```
- 优先拿到 DOI 或专利号作为可核验锚点。
- 外文 OA 全文可用 `global-biblio-base` 的 `/search/global` + 多渠道下载。

## 源 3 · CNKI（中文论文）

优先 `global-biblio-base` 技能（CNKI 索引，走 SmartLib 网关）：
- 调 `/consume` 取 token → `/search` 端点 `/search/cn`，`rule:"K=关键词"`。
- 触发词："查 CNKI 论文" → 也可直接转 `cnki-paper-search` 技能。
- 额度耗尽（429）→ 弹充值窗 + WebSearch 兜底：
  ```bash
  WebSearch: "光催化 亚氯酸盐 二氧化氯 知网"
  ```

## 源 4 · WebSearch 交叉验证

对每条关键 prior-art 做二次确认：
```bash
WebSearch: "<论文标题 / 专利号> DOI"
WebSearch: "<第一作者 年份 期刊> 亚氯酸盐 二氧化氯"
```
- 确认其真实存在、拿到稳定链接后再写入"已用清单"。
- 验证失败的标"待核验"，不计入确定性结论。

## 登录窗口（四源通用）

命中登录/验证信号时：
```bash
PY=/c/Python314/python.exe
LOGIN=/c/Users/wumin/.workbuddy/skills/patent-novelty-skill/tools/open_login.py
$PY $LOGIN --url "https://kns.cnki.net/kns8s/defaultresult/index" --title "CNKI 登录" --message "请登录后回到对话说'已登录'"
# 国知局 PSS 登录页
$PY $LOGIN --url "https://pss-system.cponline.cnipa.gov.cn/sipopublicsearch/sys/login" --title "国知局PSS登录"
# SmartLib 充值
$PY $LOGIN --url "https://1318491188-jvmi3wist0.ap-shanghai.tencentscf.com/api/pay/alipay/create" --title "SmartLib充值"
```
