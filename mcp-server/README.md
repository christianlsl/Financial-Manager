# Financial Manager MCP Server

将你的「财务管理」网站接入 AI 助手（WorkBuddy）的 MCP 服务器。网站用户通过自己的账号登录后，即可让 AI **查询数据 / 修改数据 / 生成 xlsx 账单**。

## 架构与认证模型

```
用户A 的 WorkBuddy ─┐
用户B 的 WorkBuddy ─┼─ MCP protocol (streamable-http)
用户C 的 WorkBuddy ─┘        │  可选：网关 Bearer Token (FM_MCP_TOKEN)
                             ▼
                mcp-server  (本目录，独立容器 :9911)
                             │  每用户独立 JWT（login 工具获取）
                             ▼
                backend (FastAPI :9910) ── SQLite
```

- **用户级认证**：每个用户在对话中调用 `login` 工具，提供网站上注册的邮箱和密码。MCP Server 走与前端一致的认证流程（`/auth/pubkey` → RSA-PKCS1v15 加密密码 → `/auth/login` → JWT），并按 MCP 会话缓存凭证。
- **数据隔离**：AI 的所有操作都以该用户本人的 JWT 执行，后端原有的 owner 权限隔离完整生效——用户只能看到和修改自己的数据。
- **不落盘**：用户密码只存在于会话内存中（用于 Token 过期自动重登），不写入任何文件或环境变量。
- **可选网关防护**：设置 `FM_MCP_TOKEN` 后，所有连接还需携带同一个 Bearer Token（相当于产品级访问码）；留空则只依赖用户级登录。

## 提供的能力（27 个工具）

| 类别 | 工具 |
|------|------|
| 认证 | `login` 登录、`logout` 退出、`whoami` 查看当前账号 |
| 查询 | `get_summary` 财务概览、`get_statistics` 详细统计、`list_sales`、`get_sale`、`list_purchases`、`get_purchase`、`list_customers`、`list_suppliers`、`list_companies`、`list_departments`、`list_types` |
| 修改 | `create_sale`、`update_sale`、`delete_sale`、`create_purchase`、`update_purchase`、`delete_purchase`、`create_customer`、`create_supplier`、`create_company`、`create_department`、`create_type` |
| 账单 | `generate_invoice` 单条生成、`generate_invoices_batch` 批量生成（xlsx） |

> 删除类工具描述中已提示 AI「先向用户确认再执行」；未登录时所有业务工具会返回引导登录的提示。

## 环境变量

| 变量 | 说明 | 示例 |
|------|------|------|
| `FM_API_BASE_URL` | 后端 API 地址 | 本地 `http://127.0.0.1:9910`，Docker 内 `http://backend:9910` |
| `FM_MCP_HOST` / `FM_MCP_PORT` | MCP 监听地址/端口 | `0.0.0.0` / `9911` |
| `FM_MCP_TOKEN` | 可选网关 Token；留空则仅靠用户级 login 认证 | 随机长字符串 |
| `FM_INVOICE_DIR` | 账单输出目录 | `invoices` |

> 注意：不再有 `FM_MCP_USER_EMAIL` / `FM_MCP_USER_PASSWORD`——用户凭证由最终用户在对话中提供。

## 本地调试

```bash
cd mcp-server
uv sync                     # 安装依赖
uv run financial-mcp        # 启动，监听 0.0.0.0:9911
```

用任意 MCP 客户端连接 `http://127.0.0.1:9911/mcp`；若设置了 `FM_MCP_TOKEN`，请求头需带 `Authorization: Bearer <FM_MCP_TOKEN>`。

### 本地验证（可选）

```bash
# 1) 工具级冒烟测试（需后端运行在 9910；账号通过环境变量传入）
FM_TEST_EMAIL=<邮箱> FM_TEST_PASSWORD=<密码> uv run python test_smoke.py

# 2) MCP 协议级端到端测试（需 MCP Server 已启动）
FM_TEST_EMAIL=<邮箱> FM_TEST_PASSWORD=<密码> uv run python test_protocol.py
```

> 注意：冒烟测试会在后端创建一条销售记录并自动删除，请使用专用测试账号，避免污染生产数据。

## 服务器部署（Docker Compose）

1. 在项目根目录创建 `.env`（`docker compose` 自动读取，按需配置）：

   ```bash
   # 可选：产品级访问码。所有用户的 WorkBuddy 连接时都要带上。
   # 不设则任何拿到地址的用户都可以尝试用自己的网站账号登录。
   FM_MCP_TOKEN=<随机长字符串，可留空>
   ```

2. 启动（含后端、nginx、mcp 三个服务）：

   ```bash
   docker compose up -d --build
   ```

3. 验证 MCP 端点存活：

   ```bash
   curl -X POST http://<服务器IP>:9911/mcp \
     [-H "Authorization: Bearer <FM_MCP_TOKEN>"] \
     -H "Content-Type: application/json" \
     -H "Accept: application/json, text/event-stream" \
     -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"probe","version":"0.1"}}}'
   ```

生成的账单 xlsx 会持久化在宿主机的 `./data/invoices/`。

## 用户接入 WorkBuddy（给你的网站用户的使用说明）

1. 在 WorkBuddy 中添加一个 MCP Server，类型选择 **HTTP**。
2. URL 填写：`http://<服务器IP>:9911/mcp`
3. 若你设置了 `FM_MCP_TOKEN`，鉴权方式选择 Bearer Token 并填入；否则无需鉴权配置。
4. 连接后，用户在对话中说「帮我查一下这个月的销售额」，AI 会引导用户提供网站账号密码并调用 `login` 登录，之后即可查询和操作其本人数据。

## 安全注意事项

- **传输层**：MCP 端点走 HTTP，用户密码在 `login` 时会经过网络。生产环境建议在前面加 HTTPS（nginx 反代 + TLS），或至少设置 `FM_MCP_TOKEN` 缓解裸奔风险。
- **凭证生命周期**：密码仅保存在会话内存中，`logout` 或会话结束后失效；MCP Server 重启后所有用户需重新登录。
- **会话缓存上限**：最多缓存 500 个会话的凭证（FIFO 淘汰），超出后最早的会话需要重新登录。
- **审计**：AI 的所有操作都以用户本人身份执行，后端日志可追溯到具体账号。
- 若后端 `config.yaml` 中 JWT `secret_key` 仍为默认值，请尽快修改。
