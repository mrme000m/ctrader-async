"""Async OAuth helper utilities for cTrader Open API."""

from __future__ import annotations

import asyncio
import json
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen


DEFAULT_AUTH_URI = "https://openapi.ctrader.com/apps/auth"
DEFAULT_TOKEN_URI = "https://openapi.ctrader.com/apps/token"


class OAuthHelper:
    """Helper for cTrader OAuth browser flow and token exchange.

    This helper complements protobuf-level authentication by providing
    async utilities for:
    - generating authorization URL
    - exchanging auth code for access/refresh token
    - refreshing token using HTTP endpoint
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        *,
        auth_uri: str = DEFAULT_AUTH_URI,
        token_uri: str = DEFAULT_TOKEN_URI,
        timeout: float = 30.0,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.auth_uri = auth_uri
        self.token_uri = token_uri
        self.timeout = float(timeout)

    def get_auth_uri(
        self,
        *,
        scope: str = "trading",
        state: str | None = None,
        extra_params: dict[str, Any] | None = None,
    ) -> str:
        """Build OAuth authorization URL for user redirection."""
        params: dict[str, Any] = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": scope,
        }
        if state:
            params["state"] = state
        if extra_params:
            params.update(extra_params)
        return f"{self.auth_uri}?{urlencode(params)}"

    async def exchange_code(self, auth_code: str) -> dict[str, Any]:
        """Exchange authorization code for access token payload."""
        params = {
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        return await self._request_json(self.token_uri, params)

    async def refresh_token_http(self, refresh_token: str) -> dict[str, Any]:
        """Refresh access token using OAuth token endpoint."""
        params = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        return await self._request_json(self.token_uri, params)

    async def _request_json(self, base_uri: str, params: dict[str, Any]) -> dict[str, Any]:
        query = urlencode(params)
        url = f"{base_uri}?{query}"

        def _do_request() -> dict[str, Any]:
            with urlopen(url, timeout=self.timeout) as response:  # nosec B310
                raw = response.read().decode("utf-8")
                return json.loads(raw)

        return await asyncio.to_thread(_do_request)
