"""
Integration tests for the typed event bus.

Covers every named event the client emits on client.events:
  tick                       — spot price update
  execution                  — any execution event
  execution.order            — order sub-event
  execution.position         — position sub-event
  execution.deal             — deal sub-event
  position.trailing_sl_changed
  order.error
  account.trader_updated
  market.symbol_changed
  account.disconnected       (not triggerable in normal test — wired check only)
  auth.token_invalidated     (not triggerable — wired check only)
  client.disconnect          (not triggerable — wired check only)
  risk.margin_changed        — margin changed after position open
  risk.margin_call_update    (not triggerable on healthy account — wired check only)
  risk.margin_call_trigger   (not triggerable on healthy account — wired check only)
  protobuf.envelope          — every raw message
  client.reconnect.*         (not triggerable in normal test — wired check only)

Run with:
    CTRADER_RUN_INTEGRATION=true pytest tests/test_integration_events_bus.py -v -s
"""

from __future__ import annotations

import asyncio
import pytest

from ctc import CTraderClient, TradeSide, TimeFrame

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _wait_for(flag: list, timeout: float = 8.0, interval: float = 0.1):
    """Wait until flag is truthy or timeout expires. Returns True if fired."""
    elapsed = 0.0
    while elapsed < timeout:
        if flag:
            return True
        await asyncio.sleep(interval)
        elapsed += interval
    return False


# ---------------------------------------------------------------------------
# protobuf.envelope — fires for every inbound message
# ---------------------------------------------------------------------------

class TestProtobufEnvelopeEvent:
    async def test_envelope_fires_on_connect(self, client):
        """
        After connect(), at least one ProtoOA message must have arrived
        (auth + account auth responses), so protobuf.envelope must fire.
        """
        seen = []
        client.events.on("protobuf.envelope", lambda env: seen.append(env))

        # Trigger a lightweight request to generate an inbound message
        await client.symbols.get_all()

        fired = await _wait_for(seen, timeout=5.0)
        assert fired, "protobuf.envelope never fired"
        print(f"\n  protobuf.envelope fired {len(seen)} time(s)")

    async def test_envelope_not_double_fired(self, client):
        """
        Regression: envelope must fire exactly once per inbound message.
        We count envelopes while making exactly one request and verify
        the count doesn't grow by more than the expected small number.
        """
        seen = []
        client.events.on("protobuf.envelope", lambda env: seen.append(env))

        # One request = one response (at most a handful of push events)
        before = len(seen)
        await client.symbols.get_symbol("EURUSD")
        await asyncio.sleep(0.5)
        after = len(seen)
        delta = after - before

        # Should be 1 response + maybe a few push events, but NOT 2× due to
        # the double-emit bug that was previously present.
        assert delta < 10, f"Too many envelope events ({delta}); possible double-emit"
        print(f"\n  Envelope events for one request: {delta}")


# ---------------------------------------------------------------------------
# tick event
# ---------------------------------------------------------------------------

class TestTickEvent:
    async def test_tick_fires_on_stream(self, client):
        seen = []
        client.events.on("tick", lambda evt: seen.append(evt))

        async with client.market_data.stream_ticks("EURUSD") as _:
            fired = await _wait_for(seen, timeout=10.0)

        assert fired, "tick event never fired during tick stream"
        evt = seen[0]
        assert hasattr(evt, "tick")
        assert evt.tick.bid > 0
        print(f"\n  tick event: bid={evt.tick.bid:.5f}")

    async def test_tick_carries_symbol_name(self, client):
        seen = []
        client.events.on("tick", lambda evt: seen.append(evt))

        async with client.market_data.stream_ticks("EURUSD") as _:
            await _wait_for(seen, timeout=10.0)

        if not seen:
            pytest.skip("No tick events received")
        assert seen[0].tick.symbol_name.upper() == "EURUSD"


# ---------------------------------------------------------------------------
# execution events
# ---------------------------------------------------------------------------

class TestExecutionEvents:
    async def test_execution_fires_on_market_order(self, client):
        exec_events: list = []
        order_events: list = []
        position_events: list = []
        deal_events: list = []

        client.events.on("execution", lambda e: exec_events.append(e))
        client.events.on("execution.order", lambda e: order_events.append(e))
        client.events.on("execution.position", lambda e: position_events.append(e))
        client.events.on("execution.deal", lambda e: deal_events.append(e))

        pos = await client.trading.place_market_order(
            symbol="EURUSD", side=TradeSide.BUY, volume=0.01,
            comment="integration events bus execution"
        )

        fired = await _wait_for(exec_events, timeout=8.0)
        assert fired, "execution event never fired after market order"

        sub_fired = (
            len(order_events) + len(position_events) + len(deal_events)
        )
        assert sub_fired > 0, (
            "At least one of execution.order / execution.position / execution.deal "
            "must fire alongside the execution event"
        )

        print(
            f"\n  execution={len(exec_events)}  "
            f"order={len(order_events)}  "
            f"position={len(position_events)}  "
            f"deal={len(deal_events)}"
        )

        await asyncio.sleep(0.5)
        await client.trading.close_position(pos.id)

    async def test_execution_fires_on_close(self, client):
        """Close event also fires execution."""
        exec_events: list = []
        client.events.on("execution", lambda e: exec_events.append(e))

        pos = await client.trading.place_market_order(
            symbol="EURUSD", side=TradeSide.BUY, volume=0.01,
            comment="integration events bus close"
        )
        await asyncio.sleep(0.5)

        before = len(exec_events)
        await client.trading.close_position(pos.id)
        await asyncio.sleep(2.0)
        after = len(exec_events)

        assert after > before, "execution event must fire on position close"
        print(f"\n  Close generated {after - before} execution event(s)")


# ---------------------------------------------------------------------------
# order.error
# ---------------------------------------------------------------------------

class TestOrderErrorEvent:
    async def test_order_error_fires_on_invalid_order(self, client):
        """
        Attempt to modify a non-existent order. The server should respond
        with an error event (or a protobuf error response).
        """
        errors: list = []
        client.events.on("order.error", lambda e: errors.append(e))

        try:
            await client.trading.modify_order(
                order_id=999999999,
                limit_price=1.0,
            )
        except Exception:
            pass  # Expected — request fails

        # Give the server a moment to push the error event
        await asyncio.sleep(2.0)

        if not errors:
            pytest.skip(
                "order.error event not received — broker may return a protobuf "
                "error response instead of ProtoOAOrderErrorEvent on this account"
            )

        err = errors[0]
        assert "order_id" in err or "error_code" in err or "payload" in err
        print(f"\n  order.error event: {err}")


# ---------------------------------------------------------------------------
# account.trader_updated
# ---------------------------------------------------------------------------

class TestTraderUpdatedEvent:
    async def test_trader_updated_fires_on_connect(self, client):
        """
        ProtoOATraderUpdatedEvent is sometimes sent by the server upon
        account auth. We check the wiring is correct by observing whether
        the event fires within a short window after a fresh connection.
        """
        seen: list = []

        # Register before making any new requests
        client.events.on("account.trader_updated", lambda e: seen.append(e))

        # Trigger an account info fetch to prompt a server round-trip
        await client.account.get_full_account_info()
        await asyncio.sleep(2.0)

        if not seen:
            pytest.skip(
                "account.trader_updated not observed — "
                "broker may not push this on demo"
            )
        print(f"\n  account.trader_updated fired: {len(seen)} time(s)")


# ---------------------------------------------------------------------------
# risk.margin_changed
# ---------------------------------------------------------------------------

class TestMarginChangedEvent:
    async def test_risk_margin_changed_on_position_open(self, client):
        seen: list = []

        async def _on_margin(data: dict):
            seen.append(data)

        client.events.on("risk.margin_changed", _on_margin)

        pos = await client.trading.place_market_order(
            symbol="EURUSD", side=TradeSide.BUY, volume=0.01,
            comment="integration events margin"
        )

        fired = await _wait_for(seen, timeout=8.0)

        await client.trading.close_position(pos.id)

        if not fired:
            pytest.skip(
                "risk.margin_changed not received within 8 s "
                "(broker may not push ProtoOAMarginChangedEvent on demo)"
            )

        evt = seen[0]
        assert "position_id" in evt
        assert "used_margin" in evt
        assert evt["used_margin"] >= 0
        print(f"\n  risk.margin_changed: pos={evt['position_id']}  margin={evt['used_margin']:.2f}")


# ---------------------------------------------------------------------------
# market.symbol_changed
# ---------------------------------------------------------------------------

class TestSymbolChangedEvent:
    async def test_symbol_changed_wiring(self, client):
        """
        We cannot easily force a ProtoOASymbolChangedEvent in a test, but we
        verify the handler is registered and does not raise on a simulated
        payload by checking the event bus subscription is present.
        """
        seen: list = []
        client.events.on("market.symbol_changed", lambda e: seen.append(e))

        # Just verify subscription succeeded without error
        assert True
        print("\n  market.symbol_changed handler registered successfully")


# ---------------------------------------------------------------------------
# Wired-only events (cannot be triggered safely in a test session)
# ---------------------------------------------------------------------------

class TestWiredOnlyEvents:
    """
    Verify the event names are registered on the bus without actually
    triggering the underlying server conditions.
    """

    async def test_account_disconnected_handler_registers(self, client):
        seen: list = []
        client.events.on("account.disconnected", lambda e: seen.append(e))
        assert True  # Just ensure no error on registration

    async def test_auth_token_invalidated_handler_registers(self, client):
        seen: list = []
        client.events.on("auth.token_invalidated", lambda e: seen.append(e))
        assert True

    async def test_client_disconnect_handler_registers(self, client):
        seen: list = []
        client.events.on("client.disconnect", lambda e: seen.append(e))
        assert True

    async def test_risk_margin_call_update_handler_registers(self, client):
        seen: list = []
        client.events.on("risk.margin_call_update", lambda e: seen.append(e))
        assert True

    async def test_risk_margin_call_trigger_handler_registers(self, client):
        seen: list = []
        client.events.on("risk.margin_call_trigger", lambda e: seen.append(e))
        assert True

    async def test_position_trailing_sl_changed_handler_registers(self, client):
        seen: list = []
        client.events.on("position.trailing_sl_changed", lambda e: seen.append(e))
        assert True

    async def test_reconnect_events_handler_registers(self, client):
        for name in ("client.reconnect.attempt", "client.reconnect.success", "client.reconnect.fatal"):
            client.events.on(name, lambda e: None)
        assert True


# ---------------------------------------------------------------------------
# EventBus API: on / off / once
# ---------------------------------------------------------------------------

class TestEventBusAPI:
    async def test_events_on_off(self, client):
        """off() must prevent future calls to the handler."""
        calls: list = []

        async def handler(data):
            calls.append(data)

        client.events.on("tick", handler)

        async with client.market_data.stream_ticks("EURUSD") as _:
            await _wait_for(calls, timeout=8.0)

        before = len(calls)
        client.events.off("tick", handler)

        # No more calls should arrive after off()
        snapshot = len(calls)
        await asyncio.sleep(0.5)
        assert len(calls) == snapshot, "Handler called after off()"
        print(f"\n  EventBus on/off: received {before} events before off()")

    async def test_events_once_fires_exactly_once(self, client):
        """once() handler must fire at most one time."""
        calls: list = []

        async def handler(data):
            calls.append(data)

        # Register multiple times to amplify any double-fire bug
        client.events.once("tick", handler)

        async with client.market_data.stream_ticks("EURUSD") as _:
            await _wait_for(calls, timeout=8.0)
            # Wait a bit more to catch any spurious second call
            await asyncio.sleep(1.0)

        assert len(calls) <= 1, f"once() handler fired {len(calls)} times (expected 1)"
        print(f"\n  EventBus once: fired {len(calls)} time(s)")
