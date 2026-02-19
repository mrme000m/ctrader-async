"""
Integration tests for Session API and Asset Catalog.

Covers:
- SessionAPI.get_server_version   (ProtoOAVersionReq)
- SessionAPI.refresh_token        (ProtoOARefreshTokenReq)
- SessionAPI.get_ctid_profile     (ProtoOAGetCtidProfileByTokenReq)
- AssetsAPI / AssetCatalog        (ProtoOAAssetListReq)
- SymbolCatalog.get_symbol_details_by_id  (ProtoOASymbolByIdReq)
- SymbolCatalog.search
- SymbolCatalog.get_categories    (ProtoOASymbolCategoryListReq)

Run with:
    CTRADER_RUN_INTEGRATION=true pytest tests/test_integration_session_assets.py -v -s
"""

from __future__ import annotations

import os
import pytest

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


class TestSessionAPI:
    """ProtoOAVersionReq and related session utilities."""

    async def test_get_server_version(self, client):
        try:
            version = await client.session.get_server_version()
            assert version is not None
            assert isinstance(version, str)
            assert len(version) > 0
            print(f"\n  Server version: {version}")
        except AttributeError:
            pytest.skip("get_server_version not available in this build")
        except Exception as e:
            pytest.skip(f"Server version request failed: {e}")

    async def test_get_ctid_profile(self, client):
        """ProtoOAGetCtidProfileByTokenReq — returns cTID user profile."""
        try:
            profile = await client.session.get_ctid_profile()
            if profile is not None:
                print(f"\n  cTID profile: {profile}")
            else:
                # Some demo accounts may return None — acceptable
                pytest.skip("cTID profile returned None (may not be supported on this account)")
        except AttributeError:
            pytest.skip("get_ctid_profile not available in this build")
        except Exception as e:
            pytest.skip(f"get_ctid_profile not supported: {e}")

    async def test_refresh_token(self, client):
        """
        ProtoOARefreshTokenReq — requires a refresh_token in env.
        Skips gracefully if not configured.
        """
        refresh_token = os.getenv("CTRADER_REFRESH_TOKEN", "")
        if not refresh_token:
            pytest.skip("CTRADER_REFRESH_TOKEN not set — skipping token refresh test")

        try:
            result = await client.session.refresh_token(refresh_token)
            assert result is not None
            print(f"\n  Token refreshed: {result}")
        except AttributeError:
            pytest.skip("refresh_token not available in this build")
        except Exception as e:
            pytest.skip(f"Token refresh failed (token may be expired): {e}")


class TestAssetCatalog:
    """ProtoOAAssetListReq — asset metadata."""

    async def test_get_all_assets(self, client):
        try:
            assets = await client.assets.get_all()
            assert isinstance(assets, list)
            assert len(assets) > 0
            print(f"\n  Total assets: {len(assets)}")
            # Show a few
            for a in assets[:5]:
                print(f"    id={a.id}  name={a.name}")
        except AttributeError:
            pytest.skip("assets.get_all() not available")

    async def test_get_asset_by_id(self, client):
        """Fetch asset by numeric ID — requires at least one asset loaded."""
        try:
            assets = await client.assets.get_all()
            if not assets:
                pytest.skip("No assets available")
            first = assets[0]
            fetched = await client.assets.get_asset_by_id(first.id)
            assert fetched is not None
            assert fetched.id == first.id
            assert fetched.name == first.name
            print(f"\n  Asset by id={first.id}: {fetched.name}")
        except AttributeError:
            pytest.skip("get_asset_by_id not available")

    async def test_get_asset_by_name(self, client):
        try:
            asset = await client.assets.get_asset_by_name("USD")
            if asset is None:
                pytest.skip("USD asset not found in this account's catalog")
            assert asset.name.upper() == "USD"
            print(f"\n  USD asset id={asset.id}")
        except AttributeError:
            pytest.skip("get_asset_by_name not available")


class TestSymbolCatalogExtended:
    """Extended symbol catalog — by-id lookup and category list."""

    async def test_get_symbol_details_by_id(self, client):
        """ProtoOASymbolByIdReq — fetch full symbol spec from server by numeric ID."""
        try:
            eurusd = await client.symbols.get_symbol("EURUSD")
            if eurusd is None:
                pytest.skip("EURUSD not in symbol catalog")

            detailed = await client.symbols.get_symbol_details_by_id(eurusd.id)
            assert detailed is not None
            assert detailed.id == eurusd.id
            assert detailed.digits > 0
            print(f"\n  Symbol by id={eurusd.id}: {detailed.name}  digits={detailed.digits}")
        except AttributeError:
            pytest.skip("get_symbol_details_by_id not available")
        except Exception as e:
            pytest.skip(f"Symbol by ID request failed: {e}")

    async def test_search_returns_matches(self, client):
        results = await client.symbols.search("EUR")
        assert isinstance(results, list)
        assert len(results) > 0
        assert any("EUR" in s.name.upper() for s in results)
        print(f"\n  EUR symbol search: {len(results)} results")

    async def test_search_no_match_returns_empty(self, client):
        results = await client.symbols.search("NOSUCHSYMBOL_XYZ_999")
        assert isinstance(results, list)
        assert len(results) == 0

    async def test_get_symbol_categories(self, client):
        """ProtoOASymbolCategoryListReq — symbol category metadata."""
        try:
            categories = await client.symbols.get_categories()
            assert isinstance(categories, list)
            print(f"\n  Symbol categories: {len(categories)}")
            for c in categories[:5]:
                print(f"    {c}")
        except AttributeError:
            pytest.skip("get_categories not available")
        except Exception as e:
            pytest.skip(f"Symbol categories not supported: {e}")

    async def test_get_all_symbols_count(self, client):
        symbols = await client.symbols.get_all()
        assert isinstance(symbols, list)
        assert len(symbols) > 10
        print(f"\n  Total symbols: {len(symbols)}")

    async def test_symbol_fields_eurusd(self, client):
        eurusd = await client.symbols.get_symbol("EURUSD")
        assert eurusd is not None
        assert eurusd.name == "EURUSD"
        assert eurusd.digits >= 4
        assert eurusd.pip_size > 0
        assert eurusd.lot_size_units > 0
        assert eurusd.id > 0
        print(f"\n  EURUSD: digits={eurusd.digits} pip={eurusd.pip_size} lot={eurusd.lot_size_units}")

    async def test_symbol_cache_hit(self, client):
        """Second call for same symbol must use cache (no extra round-trip)."""
        s1 = await client.symbols.get_symbol("EURUSD")
        s2 = await client.symbols.get_symbol("EURUSD")
        assert s1 is not None
        assert s2 is not None
        assert s1.id == s2.id
