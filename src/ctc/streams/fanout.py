"""Stream fanout helpers.

Provides utilities to route a single async stream into per-key queues.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import AsyncIterator, Callable, Generic, Hashable, TypeVar

T = TypeVar("T")
K = TypeVar("K", bound=Hashable)


@dataclass
class Fanout(Generic[T, K]):
    """Fanout an async iterator into per-key queues."""

    _source: AsyncIterator[T]
    _key: Callable[[T], K]
    _maxsize: int
    _drop_oldest: bool

    _queues: dict[K, asyncio.Queue[T]]
    _task: asyncio.Task | None
    _stopped: bool

    def __init__(
        self,
        source: AsyncIterator[T],
        *,
        key: Callable[[T], K],
        maxsize: int = 1000,
        drop_oldest: bool = True,
    ):
        self._source = source
        self._key = key
        self._maxsize = maxsize
        self._drop_oldest = drop_oldest
        self._queues = {}
        self._task = None
        self._stopped = False

    def queue(self, k: K) -> asyncio.Queue[T]:
        q = self._queues.get(k)
        if q is None:
            q = asyncio.Queue(maxsize=self._maxsize)
            self._queues[k] = q
        return q

    async def start(self) -> None:
        if self._task and not self._task.done():
            return
        self._stopped = False
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        self._stopped = True
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._task = None

    async def _run(self) -> None:
        async for item in self._source:
            if self._stopped:
                break
            k = self._key(item)
            q = self.queue(k)
            try:
                q.put_nowait(item)
            except asyncio.QueueFull:
                if not self._drop_oldest:
                    continue
                try:
                    _ = q.get_nowait()
                    q.task_done()
                except asyncio.QueueEmpty:
                    pass
                try:
                    q.put_nowait(item)
                except asyncio.QueueFull:
                    pass
