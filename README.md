# Sorftime MCP

把 Sorftime Enterprise API 封装成 Codex、Claude Code 等 AI Agent 可直接调用的 MCP 服务。

本项目默认使用 `stdio` 模式，本地安装后只需要配置 `SORFTIME_API_KEY`。Sorftime Account-SK 保存在使用者自己的 MCP 客户端配置或服务器环境变量中，不写入代码仓库。

## 重点

- 默认传输：`stdio`
- 本地必需环境变量：`SORFTIME_API_KEY`
- 公开 MCP 工具数：10 个
- 支持安全取数方法：32 个
- 默认站点：`domain=1`，即美国站
- 返回统一结构：`endpoint`、`domain`、`estimatedRequestCost`、`requestConsumed`、`requestLeft`、`code`、`message`、`data`、`rawResponse`
- 默认排除账户修改、订阅管理、监控任务管理类接口

## 安装方式

### npm 安装

Codex 配置：

```toml
[mcp_servers.sorftime]
command = "npx"
args = ["-y", "sorftime-mcp"]

[mcp_servers.sorftime.env]
SORFTIME_API_KEY = "你的 Sorftime Account-SK"
```

Claude Code 安装：

```bash
claude mcp add --scope user \
  -e SORFTIME_API_KEY="你的 Sorftime Account-SK" \
  sorftime -- npx -y sorftime-mcp
```

### PyPI 安装

Codex 配置：

```toml
[mcp_servers.sorftime]
command = "uvx"
args = ["sorftime-mcp"]

[mcp_servers.sorftime.env]
SORFTIME_API_KEY = "你的 Sorftime Account-SK"
```

Claude Code 安装：

```bash
claude mcp add --scope user \
  -e SORFTIME_API_KEY="你的 Sorftime Account-SK" \
  sorftime -- uvx sorftime-mcp
```

### GitHub 源码安装

```bash
uvx --from git+https://github.com/ccchenhuohuo/sorftime-mcp.git sorftime-mcp
```

对应 Codex 配置：

```toml
[mcp_servers.sorftime]
command = "uvx"
args = [
  "--from",
  "git+https://github.com/ccchenhuohuo/sorftime-mcp.git",
  "sorftime-mcp"
]

[mcp_servers.sorftime.env]
SORFTIME_API_KEY = "你的 Sorftime Account-SK"
```

## 工具列表

| 工具 | 用途 |
| --- | --- |
| `sorftime_methods` | 查看支持的方法、分类、消耗、是否异步、是否有快捷工具 |
| `sorftime_method_schema` | 查看单个方法的参数、示例、站点映射和消耗说明 |
| `sorftime_call` | 白名单路由工具，用于调用低频安全取数方法 |
| `product_request` | 产品详情，对应 `ProductRequest` |
| `category_request` | 类目 Top 100，对应 `CategoryRequest` |
| `keyword_request` | 关键词详情，对应 `KeywordRequest` |
| `product_query` | 产品搜索，对应 `ProductQuery` |
| `category_trend` | 类目趋势，对应 `CategoryTrend` |
| `request_stream_month` | Request 使用和余额，对应 `RequestStreamMonth` |
| `coin_query` | 积分余额，对应 `CoinQuery` |

高频场景优先使用快捷工具。低频场景使用 `sorftime_call`，先用 `sorftime_methods` 和 `sorftime_method_schema` 查询 method 和参数。

## 调用示例

查询产品详情：

```json
{
  "input": {
    "asin": "B0CVM8TXHP",
    "domain": 1,
    "trend": 1
  }
}
```

通过路由查询销量估算：

```json
{
  "input": {
    "method": "AsinSalesVolume",
    "domain": 1,
    "params": {
      "ASIN": "B0CVM8TXHP",
      "Page": 1
    }
  }
}
```

查看某个方法的参数：

```json
{
  "input": {
    "method": "ProductRequest"
  }
}
```

## 站点映射

| domain | 站点 |
| --- | --- |
| 1 | US 美国 |
| 2 | GB 英国 |
| 3 | DE 德国 |
| 4 | FR 法国 |
| 5 | IN 印度 |
| 6 | CA 加拿大 |
| 7 | JP 日本 |
| 8 | ES 西班牙 |
| 9 | IT 意大利 |
| 10 | MX 墨西哥 |
| 11 | AE 阿联酋 |
| 12 | AU 澳大利亚 |
| 13 | BR 巴西 |
| 14 | SA 沙特阿拉伯 |

IN、AE、AU、BR、SA 不支持历史数据回填。

## 返回结构

所有真实 Sorftime 请求都返回统一结构：

```json
{
  "endpoint": "ProductRequest",
  "domain": 1,
  "estimatedRequestCost": 1,
  "requestConsumed": 1,
  "requestLeft": 1200,
  "code": 0,
  "message": null,
  "data": {},
  "rawResponse": {}
}
```

Agent 应优先读取 `code`、`message`、`data`、`requestConsumed` 和 `requestLeft`。

## 安全边界

v1 只开放安全取数接口，默认不开放：

- 收藏词新增、修改、删除等账户状态变更接口
- 关键词监控、榜单监控、跟卖库存监控、ASIN 订阅等订阅管理接口
- 消耗监控点数或订阅点数、但不属于通用取数的接口

## 审计日志

默认不向标准输出写日志，避免污染 MCP stdio 协议。需要审计记录时，通过环境变量写入本地 JSONL 文件：

```bash
SORFTIME_AUDIT_LOG_PATH=logs/sorftime-mcp-audit.jsonl
```

审计日志会记录 endpoint、domain、参数摘要、估算消耗、实际消耗、剩余 Request、耗时和 Sorftime 返回码。日志不会记录 Sorftime Account-SK。

## 仓库

```text
https://github.com/ccchenhuohuo/sorftime-mcp
```
