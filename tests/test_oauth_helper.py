from __future__ import annotations

import pytest

from ctc.auth.oauth import OAuthHelper


@pytest.mark.asyncio
async def test_get_auth_uri_contains_required_params():
    helper = OAuthHelper(
        client_id="cid",
        client_secret="secret",
        redirect_uri="https://example.com/callback",
    )

    uri = helper.get_auth_uri(scope="trading", state="xyz")

    assert "client_id=cid" in uri
    assert "redirect_uri=https%3A%2F%2Fexample.com%2Fcallback" in uri
    assert "scope=trading" in uri
    assert "state=xyz" in uri


@pytest.mark.asyncio
async def test_exchange_and_refresh_delegate_to_request_json(monkeypatch):
    helper = OAuthHelper(
        client_id="cid",
        client_secret="secret",
        redirect_uri="https://example.com/callback",
    )

    async def fake_request_json(base_uri, params):
        if params.get("grant_type") == "authorization_code":
            return {"accessToken": "a", "refreshToken": "r"}
        return {"accessToken": "a2", "refreshToken": "r2"}

    monkeypatch.setattr(helper, "_request_json", fake_request_json)

    exchanged = await helper.exchange_code("auth-code")
    refreshed = await helper.refresh_token_http("old-refresh")

    assert exchanged["accessToken"] == "a"
    assert refreshed["refreshToken"] == "r2"
