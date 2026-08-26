"""End-to-end MCP protocol test against a running server.

Requires env vars:
  FM_MCP_URL       (default http://127.0.0.1:9911/mcp)
  FM_TEST_EMAIL    (a real account on the backend)
  FM_TEST_PASSWORD
  FM_MCP_TOKEN     (optional; only if the server sets a gateway token)

Run: uv run python test_protocol.py
"""

import asyncio
import json
import os

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

URL = os.environ.get("FM_MCP_URL", "http://127.0.0.1:9911/mcp")
TOKEN = os.environ.get("FM_MCP_TOKEN", "")
EMAIL = os.environ.get("FM_TEST_EMAIL", "")
PASSWORD = os.environ.get("FM_TEST_PASSWORD", "")

if not EMAIL or not PASSWORD:
    raise SystemExit("请设置 FM_TEST_EMAIL / FM_TEST_PASSWORD 环境变量")


async def run_session(email: str, password: str, do_login: bool, label: str):
    """Run one MCP session; returns summary lines."""
    headers = {"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}
    async with streamablehttp_client(URL, headers=headers) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print(f"[OK] initialize ({label})")

            tools = await session.list_tools()
            names = [t.name for t in tools.tools]
            print(f"[OK] tools/list ({label}): {len(names)} tools")
            assert "login" in names, "login tool missing"
            assert len(names) == 27, f"expected 27, got {len(names)}"

            # Before login, business tools must fail with a friendly message.
            res = await session.call_tool("get_summary", {})
            err = res.isError
            if do_login:
                assert err, "get_summary should fail before login"
                print(f"[OK] blocked before login ({label}):",
                      res.content[0].text[:50])

                res = await session.call_tool(
                    "login", {"email": email, "password": password}
                )
                assert not res.isError, res.content[0].text
                print(f"[OK] login ({label}):", res.content[0].text[:60])

                res = await session.call_tool("whoami", {})
                me = json.loads(res.content[0].text)
                assert me.get("email") == email
                print(f"[OK] whoami ({label}): {me.get('email')}")

            # Query after login (or expected failure if not logged in)
            res = await session.call_tool("get_summary", {})
            if do_login:
                assert not res.isError
                print(f"[OK] get_summary ({label}):",
                      res.content[0].text[:80])
            else:
                assert res.isError
                print(f"[OK] still blocked ({label}):",
                      res.content[0].text[:50])
                return

            # Query with params
            res = await session.call_tool("list_sales", {"limit": 3})
            data = json.loads(res.content[0].text)
            print(f"[OK] list_sales ({label}): total={data['total']}")

            # Date-typed param conversion via protocol (string input)
            res = await session.call_tool(
                "get_statistics",
                {"analysis_type": "monthly",
                 "date_from": "2026-01-01", "date_to": "2026-12-31"},
            )
            assert not res.isError
            print(f"[OK] get_statistics with date strings ({label})")

            # Mutation
            res = await session.call_tool(
                "create_sale",
                {
                    "date": "2026-08-26",
                    "item_name": "协议测试商品",
                    "items_count": 2,
                    "unit_price": 10.0,
                },
            )
            created = json.loads(res.content[0].text)
            sale_id = created["id"]
            print(f"[OK] create_sale ({label}): id={sale_id}")

            # Invoice with attachment
            res = await session.call_tool("generate_invoice", {"sale_id": sale_id})
            has_attachment = any(b.type == "resource" for b in res.content)
            print(f"[OK] generate_invoice attachment ({label}):", has_attachment)
            assert has_attachment

            # Cleanup
            res = await session.call_tool("delete_sale", {"sale_id": sale_id})
            assert not res.isError
            print(f"[OK] delete_sale cleanup ({label})")


async def main():
    # Session 1: login and use tools.
    await run_session(EMAIL, PASSWORD, do_login=True, label="user1")

    # Session 2: never logs in - must stay blocked (isolation check).
    await run_session(EMAIL, PASSWORD, do_login=False, label="user2-not-logged-in")

    print("\nAll protocol checks passed.")


if __name__ == "__main__":
    asyncio.run(main())
