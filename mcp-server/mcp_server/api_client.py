"""HTTP client for the Financial Manager backend REST API.

Each MCP session (i.e. each connected user) gets its own ``ApiClient``.
Credentials are supplied by the end user through the ``login`` tool -
never stored in environment variables.

Authentication flow per user (same as the web frontend):
  1. GET /auth/pubkey        -> RSA-2048 public key (PEM)
  2. RSA-PKCS1v15 encrypt the user's password
  3. POST /auth/login        -> JWT access_token
  4. Every request sends `Authorization: Bearer <jwt>`.

On a 401 response the client re-authenticates once (using the password
held in memory for the session) and retries. It also honours the
backend's sliding-refresh `X-New-Token` header.
"""

from __future__ import annotations

import base64
import logging
import threading
from typing import Any

import httpx
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding

from .config import settings

logger = logging.getLogger(__name__)

# Cap the number of cached sessions to bound memory usage. Oldest entries
# are evicted first (simple FIFO - stale sessions that reconnect simply
# log in again).
_MAX_SESSIONS = 500


class BackendError(RuntimeError):
    """Raised when the backend returns a non-2xx response."""

    def __init__(self, status_code: int, detail: Any, path: str):
        self.status_code = status_code
        self.detail = detail
        self.path = path
        message = detail if isinstance(detail, str) else str(detail)
        super().__init__(
            f"后端接口 {path} 返回错误 (HTTP {status_code}): {message}"
        )


class NotLoggedInError(RuntimeError):
    """Raised when a tool is called before the user logged in."""

    def __init__(self) -> None:
        super().__init__(
            "尚未登录。请先调用 login 工具，提供网站注册的邮箱和密码，"
            "登录后即可查询和操作你自己的数据。"
        )


class ApiClient:
    """Thin wrapper around the backend REST API, bound to one user."""

    def __init__(self, base_url: str, email: str, password: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.email = email
        self.password = password
        self._token: str | None = None
        self._public_key_pem: str | None = None

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------
    def _get_public_key(self) -> str:
        """Fetch and cache the RSA public key PEM from the backend."""
        if self._public_key_pem:
            return self._public_key_pem
        resp = httpx.get(f"{self.base_url}/auth/pubkey", timeout=15)
        resp.raise_for_status()
        self._public_key_pem = resp.json()["pem"]
        return self._public_key_pem

    def _encrypt_password(self) -> str:
        """Encrypt the plaintext password with RSA-PKCS1v15 (jsencrypt-compatible)."""
        pem = self._get_public_key()
        public_key = serialization.load_pem_public_key(pem.encode("utf-8"))
        ciphertext = public_key.encrypt(
            self.password.encode("utf-8"),
            padding.PKCS1v15(),
        )
        return base64.b64encode(ciphertext).decode("ascii")

    def authenticate(self) -> None:
        """Log in with the user's credentials and store the JWT."""
        enc_password = self._encrypt_password()
        resp = httpx.post(
            f"{self.base_url}/auth/login",
            json={"email": self.email, "enc_password": enc_password},
            timeout=15,
        )
        if resp.status_code >= 400:
            detail = resp.json().get("detail", "unknown error")
            raise BackendError(resp.status_code, detail, "/auth/login")
        self._token = resp.json()["access_token"]
        logger.info("User %s authenticated against %s", self.email, self.base_url)

    # ------------------------------------------------------------------
    # Request helpers
    # ------------------------------------------------------------------
    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict | None = None,
        json: dict | None = None,
        retry: bool = True,
    ) -> dict | list:
        if not self._token:
            self.authenticate()

        url = f"{self.base_url}{path}"
        headers = {"Authorization": f"Bearer {self._token}"}
        resp = httpx.request(
            method, url, headers=headers, params=params, json=json, timeout=30
        )

        # Sliding refresh: backend issues a fresh token in a response header.
        new_token = resp.headers.get("X-New-Token")
        if new_token:
            self._token = new_token

        if resp.status_code == 401 and retry:
            logger.info("Token expired, re-authenticating and retrying %s", path)
            self.authenticate()
            return self._request(method, path, params=params, json=json, retry=False)

        if resp.status_code >= 400:
            try:
                detail = resp.json().get("detail", resp.text)
            except Exception:
                detail = resp.text
            raise BackendError(resp.status_code, detail, path)

        if resp.status_code == 204:
            return {}
        return resp.json()

    def get(self, path: str, **kwargs) -> dict | list:
        return self._request("GET", path, **kwargs)

    def post(self, path: str, **kwargs) -> dict | list:
        return self._request("POST", path, **kwargs)

    def put(self, path: str, **kwargs) -> dict | list:
        return self._request("PUT", path, **kwargs)

    def delete(self, path: str, **kwargs) -> dict | list:
        return self._request("DELETE", path, **kwargs)

    def get_token(self) -> str | None:
        return self._token


# ----------------------------------------------------------------------
# Per-session client registry
# ----------------------------------------------------------------------
_sessions: dict[Any, ApiClient] = {}
_lock = threading.Lock()


def login(session_id: Any, email: str, password: str) -> ApiClient:
    """Authenticate a user for the given MCP session and cache the client.

    Raises BackendError on wrong credentials.
    """
    client = ApiClient(
        base_url=settings.api_base_url, email=email, password=password
    )
    client.authenticate()
    with _lock:
        # Evict oldest sessions when the cache is full.
        while len(_sessions) >= _MAX_SESSIONS:
            _sessions.pop(next(iter(_sessions)))
        _sessions[session_id] = client
    return client


def logout(session_id: Any) -> bool:
    """Drop the cached client for a session. Returns True if it existed."""
    with _lock:
        return _sessions.pop(session_id, None) is not None


def get_client(session_id: Any) -> ApiClient:
    """Return the ApiClient bound to the session, or raise NotLoggedInError."""
    with _lock:
        client = _sessions.get(session_id)
    if client is None:
        raise NotLoggedInError()
    return client


def session_key(ctx) -> Any:
    """Stable identity for an MCP session, derived from the Context object.

    FastMCP 1.x does not expose the transport-level session id to tools,
    but the ServerSession object is stable for the lifetime of one MCP
    session. We use the object itself as the dict key (identity hash) -
    this avoids `id()` reuse after garbage collection, at the cost of
    keeping a strong reference until the entry is evicted (bounded by
    _MAX_SESSIONS).
    """
    return ctx.session
