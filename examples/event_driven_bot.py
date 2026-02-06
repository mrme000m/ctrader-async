"""Example: Event-driven bot skeleton.

This demonstrates the recommended integration pattern:

- Use `client.events` (EventBus) instead of polling.
- Enable `ModelEventBridge` to convert low-level execution lifecycle events
  into stable domain models (`model.order`, `model.position`, `model.deal`).
- Enable `TradingStateCacheUpdater` to keep `TradingAPI` caches warm using model events.

The example is intentionally passive (it does not trade) but shows where to plug
in your strategy.
"""

from __future__ import annotations

import asyncio
import signal

from ctc import CTraderClient
from ctc.utils import ModelEventBridge, TradingStateCacheUpdater


async def main() -> None:
    stop = asyncio.Event()

    def _request_stop(*_args) -> None:
        stop.set()

    # Graceful shutdown on SIGINT/SIGTERM
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _request_stop)
        except NotImplementedError:
            # Windows ProactorEventLoop
            pass

    async with CTraderClient.from_env(auto_enable_features=False) as client:
        print("✅ Connected")

        # Enable model bridge + state cache updater.
        bridge = ModelEventBridge(client.events, client.symbols, client.trading)
        bridge.enable()

        cache_updater = TradingStateCacheUpdater(client.events, client.trading)
        cache_updater.enable()

        # --- Optional: raw protobuf envelope tap (debugging) ---
        # async def log_env(env):
        #     print("envelope payloadType=", env.payloadType, "clientMsgId=", getattr(env, "clientMsgId", ""))
        # client.events.on("protobuf.envelope", log_env)

        # --- Strategy hooks: subscribe to model events ---
        async def on_order(order) -> None:
            # Example: update internal state, metrics, etc.
            print("order", getattr(order, "id", None), getattr(order, "symbol_name", None), getattr(order, "volume", None))

        async def on_position(pos) -> None:
            print("position", getattr(pos, "id", None), getattr(pos, "symbol_name", None), getattr(pos, "volume", None))

        async def on_deal(deal) -> None:
            print("deal", getattr(deal, "deal_id", None), getattr(deal, "symbol_name", None), getattr(deal, "volume", None))

        async def on_exec_error(err) -> None:
            print("execution_error", getattr(err, "error_code", None))

        client.events.on("model.order", on_order)
        client.events.on("model.position", on_position)
        client.events.on("model.deal", on_deal)
        client.events.on("model.execution_error", on_exec_error)

        # Optional: subscribe to the raw execution lifecycle layer
        # client.events.on("execution.order", lambda e: print("execution.order", e.order_id))

        print("🟢 Bot running. Waiting for events...")
        await stop.wait()
        print("🛑 Stopping...")


if __name__ == "__main__":
    asyncio.run(main())
