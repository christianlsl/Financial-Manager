"""Financial Manager MCP Server configuration.

All settings are read from environment variables (see .env.example).
User credentials are NOT configured here - end users authenticate via
the `login` tool with their own website account.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the mcp-server directory when running locally
load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default).strip()


class Settings:
    """Runtime configuration for the MCP server."""

    # --- Backend API (existing Financial Manager REST API) ---
    # In docker-compose this is http://backend:9910
    api_base_url: str = _env("FM_API_BASE_URL", "http://127.0.0.1:9910")

    # --- MCP server (streamable-http) ---
    host: str = _env("FM_MCP_HOST", "0.0.0.0")
    port: int = int(_env("FM_MCP_PORT", "9911"))

    # Optional gateway token protecting the MCP endpoint itself.
    # If set, clients must send `Authorization: Bearer <token>` on top of
    # the per-user `login`. Use it when you want a shared "access code"
    # for your product's users. If empty, only per-user login applies.
    mcp_token: str = _env("FM_MCP_TOKEN", "")

    # --- Invoice generation ---
    # Directory where generated .xlsx invoices are also saved on disk.
    invoice_dir: Path = Path(_env("FM_INVOICE_DIR", "invoices"))

    def validate(self) -> None:
        if not self.api_base_url.startswith(("http://", "https://")):
            raise RuntimeError("FM_API_BASE_URL must start with http:// or https://")
        self.invoice_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()
