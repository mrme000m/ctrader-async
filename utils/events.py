"""Event bus and hook utilities.

This module provides a lightweight async event system suitable for:
- trading bots/agents
- MCP clients
- application-level observability & integrations

Design goals:
- no external dependencies
- safe: exceptions in subscribers do not crash the client
- flexible: supports both typed events (dataclasses) and raw protobuf envelopes
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, DefaultDict, Generic, Optional, TypeVar
from collections import defaultdict

logger = logging.getLogger(__name__)

T = TypeVar("T")

EventHandler = Callable[[Any], Awaitable[None] | None]


class EventBus:
    """Simple async event bus.

    Handlers can be sync or async. Emission never raises; handler errors are logged.
    """

    def __init__(self):
        self._handlers: DefaultDict[str, list[EventHandler]] = defaultdict(list)

    def on(self, event_name: str, handler: EventHandler) -> None:
        self._handlers[event_name].append(handler)

    def off(self, event_name: str, handler: EventHandler) -> None:
        if handler in self._handlers.get(event_name, []):
            self._handlers[event_name].remove(handler)

    async def emit(self, event_name: str, event: Any) -> None:
        handlers = list(self._handlers.get(event_name, []))
        if not handlers:
            return

        tasks = [self._safe_call(h, event_name, event) for h in handlers]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _safe_call(self, handler: EventHandler, event_name: str, event: Any) -> None:
        try:
            res = handler(event)
            if asyncio.iscoroutine(res):
                await res
        except Exception as exc:
            logger.error(f"Event handler error for {event_name}: {exc}", exc_info=True)


@dataclass(frozen=True)
class HookContext:
    """Context passed to hooks."""

    name: str
    data: dict[str, Any]


Hook = Callable[[HookContext], Awaitable[None] | None]


class HookManager:
    """Named hook points for customizing behavior.

    Hooks are called sequentially (to preserve deterministic order), and errors are logged.
    """

    def __init__(self):
        self._hooks: DefaultDict[str, list[Hook]] = defaultdict(list)

    def register(self, hook_name: str, hook: Hook) -> None:
        self._hooks[hook_name].append(hook)

    def unregister(self, hook_name: str, hook: Hook) -> None:
        if hook in self._hooks.get(hook_name, []):
            self._hooks[hook_name].remove(hook)

    async def run(self, hook_name: str, **data: Any) -> None:
        hooks = list(self._hooks.get(hook_name, []))
        if not hooks:
            return

        ctx = HookContext(name=hook_name, data=dict(data))
        for hook in hooks:
            try:
                res = hook(ctx)
                if asyncio.iscoroutine(res):
                    await res
            except Exception as exc:
                logger.error(f"Hook error for {hook_name}: {exc}", exc_info=True)
