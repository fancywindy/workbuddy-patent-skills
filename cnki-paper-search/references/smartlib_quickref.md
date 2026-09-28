# SmartLib `/search/cn` 快速参考（CNKI 索引）

网关配置来自 `global-biblio-base/config.json`：
- `SMARTLIB_GATEWAY_URL`：https://1318491188-jvmi3wist0.ap-shanghai.tencentscf.com
- `SMARTLIB_GATEWAY_SECRET`：在 config.json 中（勿在对话泄露）
- `SMARTLIB_EMAIL`：在 config.json 中配置（缺失则向用户索取，禁止臆造）

## 调用链（每次计费接口都需先 /consume）

```
① POST {URL}/consume
   Headers: Authorization: Bearer <SECRET>
   Body:    {"email":"<EMAIL>", "skill_source":"cnki-paper-search"}
   → 200 返回 consume_token；429 额度耗尽

② POST {URL}/search
   Headers: Authorization: Bearer <SECRET>
   Content-Type: application/json
   Body: {
     "email":"<EMAIL>",
     "consume_token":"<token>",
     "skill_source":"cnki-paper-search",
     "endpoint":"/search/cn",            // CNKI 中文期刊索引
     "rule":"K=二氧化氯 催化",            // 检索表达式
     "page_index":1,
     "page_size":20
   }
   → 200 检索结果；401 token 过期/已用，需重新 /consume
```

- 令牌单次使用、约 60s 有效；过期/已用返回 401，重新 /consume 即可。
- 配额仅成功调用后扣除；失败不扣。
- 额度耗尽（429）→ 弹充值窗（见 SKILL.md 登录窗口）+ WebSearch 兜底。
- 完整字段说明见 `global-biblio-base/SKILL.md`。

## 直接复现（无需 Python 包装）

可用 `curl` 复现以上两步；日常用 `tools/smartlib_cn_search.py` 更省事（自动读 config、自动 consume→search）。
