# Sorftime MCP

[![PyPI 版本](https://img.shields.io/pypi/v/sorftime-mcp)](https://pypi.org/project/sorftime-mcp/)
[![npm 版本](https://img.shields.io/npm/v/sorftime-mcp)](https://www.npmjs.com/package/sorftime-mcp)

面向 Codex、Claude Code 和其他 MCP 客户端的 Sorftime Enterprise API 取数服务。

Sorftime MCP 以 `stdio` 方式运行，把 Sorftime 的产品、类目、关键词、积分和 Request 使用数据封装成 AI Agent 可直接调用的工具。使用者只需要在 MCP 客户端中配置 `SORFTIME_API_KEY`，不需要编写接口请求代码，也不需要在项目中保存 Sorftime Account-SK。

## 目录

- [为什么使用](#为什么使用)
- [能力概览](#能力概览)
- [安装前置条件](#安装前置条件)
- [Codex 安装](#codex-安装)
- [Claude Code 安装](#claude-code-安装)
- [工具体系](#工具体系)
- [调用示例](#调用示例)
- [站点映射](#站点映射)
- [返回结构](#返回结构)
- [安全边界](#安全边界)

## 为什么使用

- Agent 原生：工具命名、参数结构和返回格式面向 AI Agent 调用设计。
- 小工具面：只公开 10 个 MCP 工具，降低 Agent 选错工具的概率。
- 覆盖安全取数：通过 `sorftime_call` 白名单路由覆盖 32 个安全 Sorftime 方法。
- 可发现 schema：Agent 可以先查询 `sorftime_methods` 和 `sorftime_method_schema`，再决定调用方式。
- 统一返回：所有真实 Sorftime 请求都返回相同 envelope，便于后续分析、审计和错误处理。
- 凭证隔离：Sorftime Account-SK 只放在 MCP 客户端环境变量中，不写入仓库。

## 能力概览

| 项目 | 当前状态 |
| --- | --- |
| 传输方式 | `stdio` |
| 必需环境变量 | `SORFTIME_API_KEY` |
| 公开 MCP 工具 | 10 个 |
| 安全取数方法 | 32 个 |
| 默认站点 | `domain=1`，US 美国站 |
| 包发布 | PyPI：`sorftime-mcp`；npm：`sorftime-mcp` |
| 返回格式 | `endpoint`、`domain`、`estimatedRequestCost`、`requestConsumed`、`requestLeft`、`code`、`message`、`data`、`rawResponse` |

## 安装前置条件

使用前需要准备：

- Sorftime Account-SK
- `uvx`
- Node.js / `npx`，仅在使用 npm 安装方式时需要

检查本机是否已有 `uvx`：

```bash
uvx --version
```

检查本机是否已有 `npx`：

```bash
npx --version
```

> npm 包当前是一个轻量启动器，会调用 `uvx` 运行 PyPI 上的 Python MCP 包。因此使用 `npx -y sorftime-mcp` 时，本机也必须已经安装 `uvx`。

## Codex 安装

### 通过 PyPI

```toml
[mcp_servers.sorftime]
command = "uvx"
args = ["sorftime-mcp"]

[mcp_servers.sorftime.env]
SORFTIME_API_KEY = "你的 Sorftime Account-SK"
```

### 通过 npm

```toml
[mcp_servers.sorftime]
command = "npx"
args = ["-y", "sorftime-mcp"]

[mcp_servers.sorftime.env]
SORFTIME_API_KEY = "你的 Sorftime Account-SK"
```

### 通过 GitHub 源码

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

## Claude Code 安装

### 通过 PyPI

```bash
claude mcp add --scope user \
  -e SORFTIME_API_KEY="你的 Sorftime Account-SK" \
  sorftime -- uvx sorftime-mcp
```

### 通过 npm

```bash
claude mcp add --scope user \
  -e SORFTIME_API_KEY="你的 Sorftime Account-SK" \
  sorftime -- npx -y sorftime-mcp
```

### 通过 GitHub 源码

```bash
claude mcp add --scope user \
  -e SORFTIME_API_KEY="你的 Sorftime Account-SK" \
  sorftime -- uvx --from git+https://github.com/ccchenhuohuo/sorftime-mcp.git sorftime-mcp
```

## 工具体系

Sorftime MCP 使用三层工具结构：

| 层级 | 工具 | 用途 |
| --- | --- | --- |
| 发现 | `sorftime_methods` | 查看支持的方法、分类、消耗、是否异步、是否有快捷工具 |
| 发现 | `sorftime_method_schema` | 查看单个方法的参数、示例、站点映射和消耗说明 |
| 路由 | `sorftime_call` | 白名单路由工具，用于调用低频安全取数方法 |
| 快捷 | `product_request` | 产品详情，对应 `ProductRequest` |
| 快捷 | `category_request` | 类目 Top 100，对应 `CategoryRequest` |
| 快捷 | `keyword_request` | 关键词详情，对应 `KeywordRequest` |
| 快捷 | `product_query` | 产品搜索，对应 `ProductQuery` |
| 快捷 | `category_trend` | 类目趋势，对应 `CategoryTrend` |
| 快捷 | `request_stream_month` | Request 使用和余额，对应 `RequestStreamMonth` |
| 快捷 | `coin_query` | 积分余额，对应 `CoinQuery` |

常用查询优先使用快捷工具。低频查询通过 `sorftime_call` 调用，调用前先用 `sorftime_methods` 和 `sorftime_method_schema` 确认 method、参数和 request 消耗。

## 调用示例

### 查询产品详情

```json
{
  "input": {
    "asin": "B0CVM8TXHP",
    "domain": 1,
    "trend": 1
  }
}
```

### 通过路由查询销量估算

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

### 查看方法 schema

```json
{
  "input": {
    "method": "ProductRequest"
  }
}
```

## 站点映射

所有工具默认使用 `domain=1`。

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

Agent 应优先读取：

- `code`：Sorftime 返回码
- `message`：Sorftime 返回消息
- `data`：业务数据
- `requestConsumed`：本次实际消耗
- `requestLeft`：剩余 Request

## 安全边界

当前版本只开放安全取数接口，默认不开放：

- 收藏词新增、修改、删除等账户状态变更接口
- 关键词监控、榜单监控、跟卖库存监控、ASIN 订阅等订阅管理接口
- 消耗监控点数或订阅点数、但不属于通用取数的接口

Sorftime Account-SK 不应该写入 README、Issue、PR、聊天记录或代码仓库。只应放在 MCP 客户端配置的环境变量中。

## 审计日志

默认不向标准输出写日志，避免污染 MCP stdio 协议。需要审计记录时，通过环境变量写入本地 JSONL 文件：

```bash
SORFTIME_AUDIT_LOG_PATH=logs/sorftime-mcp-audit.jsonl
```

审计日志会记录 endpoint、domain、参数摘要、估算消耗、实际消耗、剩余 Request、耗时和 Sorftime 返回码。日志不会记录 Sorftime Account-SK。

## 项目链接

- GitHub：[ccchenhuohuo/sorftime-mcp](https://github.com/ccchenhuohuo/sorftime-mcp)
- PyPI：[sorftime-mcp](https://pypi.org/project/sorftime-mcp/)
- npm：[sorftime-mcp](https://www.npmjs.com/package/sorftime-mcp)
