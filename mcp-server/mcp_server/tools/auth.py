"""User authentication tools.

Each MCP session (one connected user's WorkBuddy client) must call
``login`` first with the user's own Financial Manager website account.
The JWT is then cached for the session and every other tool operates
with that user's identity and data isolation.
"""

from __future__ import annotations

from mcp.server.fastmcp import Context

from ..api_client import get_client, login as _login, logout as _logout, session_key


def login(email: str, password: str, ctx: Context) -> str:
    """登录财务管理账号（使用网站上注册的邮箱和密码）。

    必须先登录才能使用其他工具。登录后，后续所有查询和操作都将以
    你本人的身份进行，只能看到和修改你自己的数据。

    Args:
        email: 网站注册邮箱。
        password: 账号密码（明文传输到 MCP Server 后经 RSA 加密提交后端）。
    """
    client = _login(session_key(ctx), email, password)
    user = client.get("/auth/me")
    company = user.get("company_name") or "未设置公司"
    return f"登录成功。欢迎，{company}（{email}）。现在可以查询和操作你的财务数据了。"


def logout(ctx: Context) -> str:
    """退出登录，清除本会话保存的凭证。"""
    if _logout(session_key(ctx)):
        return "已退出登录，本会话的凭证已清除。"
    return "当前会话本来就未登录。"


def whoami(ctx: Context) -> str:
    """查看当前会话登录的账号信息。"""
    user = get_client(session_key(ctx)).get("/auth/me")
    import json

    return json.dumps(user, ensure_ascii=False, default=str)
