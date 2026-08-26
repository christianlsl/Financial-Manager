"""Financial Manager MCP Server entry point.

Runs a FastMCP server over streamable-http so remote MCP clients
(e.g. WorkBuddy) can call the Financial Manager's business APIs through
natural language.

Start it with:  financial-mcp
or:             python -m mcp_server.main
"""

from __future__ import annotations

import logging

from .config import settings
from .tools import ALL_TOOLS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("financial-mcp")


class TokenAuthMiddleware:
    """Optional ASGI middleware protecting the MCP endpoint with a Bearer token.

    If FM_MCP_TOKEN is set, every request must carry
    `Authorization: Bearer <FM_MCP_TOKEN>` (a shared gateway password for
    your product's users, on top of the per-user `login` tool).
    If it is empty, the endpoint relies solely on per-user authentication
    via the `login` tool.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        expected = settings.mcp_token
        if (
            expected
            and scope["type"] == "http"
            and not self._is_authorized(scope, expected)
        ):
            from starlette.responses import JSONResponse

            response = JSONResponse(
                status_code=401, content={"detail": "unauthorized"}
            )
            await response(scope, receive, send)
            return
        await self.app(scope, receive, send)

    @staticmethod
    def _is_authorized(scope, expected: str) -> bool:
        headers = dict(scope.get("headers") or [])
        auth = headers.get(b"authorization", b"").decode("utf-8")
        return auth == f"Bearer {expected}"


def _build_mcp():
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "mcp 依赖未安装，请先执行 `uv sync` 或 `pip install -e .`"
        ) from exc

    instructions = (
        "你是「财务管理」AI 助手。用户首次使用时，请先请用户提供网站注册的"
        "邮箱和密码并调用 login 工具登录；未登录时其他工具会返回需要登录的提示。"
        "登录后，你可以查询销售、采购、客户、供应商、公司、部门、业务类型以及"
        "财务统计；可以创建/修改/删除销售和采购记录；可以创建客户、供应商、公司、"
        "部门、业务类型；还可以根据销售记录生成正式的 xlsx 账单。"
        "每个用户只能看到和操作自己的数据。涉及删除操作时，请先向用户确认。"
        "请勿在对话中主动记录或复述用户的密码。"
    )

    mcp = FastMCP(
        "financial-manager",
        instructions=instructions,
        host=settings.host,
        port=settings.port,
    )

    for module, tool_name in ALL_TOOLS:
        mcp.add_tool(getattr(module, tool_name))

    return mcp


mcp = _build_mcp()


def app():
    """Return the wrapped ASGI application (token-guarded FastMCP server)."""
    inner = mcp.streamable_http_app()
    return TokenAuthMiddleware(inner)


def main() -> None:
    """Entry point: validate config and start the streamable-http server."""
    import uvicorn

    settings.validate()
    logger.info(
        "Financial Manager MCP server starting on %s:%s -> %s",
        settings.host,
        settings.port,
        settings.api_base_url,
    )
    if settings.mcp_token:
        logger.info("FM_MCP_TOKEN 已配置，MCP 端点启用网关级 Bearer 鉴权。")
    else:
        logger.info(
            "FM_MCP_TOKEN 未配置，仅依赖用户级 login 工具认证。"
            "如需网关级防护请设置 FM_MCP_TOKEN。"
        )
    uvicorn.run(
        app(),
        host=settings.host,
        port=settings.port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
