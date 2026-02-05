"""Small async concurrency helpers."""

from __future__ import annotations

import asyncio
from typing import Awaitable, Callable, Iterable, TypeVar

T = TypeVar("T")


async def gather_limited(
    coros: Iterable[Callable[[], Awaitable[T]]],
    *,
    limit: int = 10,
    return_exceptions: bool = True,
) -> list[T]:
    """Run coroutine factories with a concurrency limit."""

    sem = asyncio.Semaphore(max(1, int(limit)))

    async def run_one(factory: Callable[[], Awaitable[T]]) -> T:
        async with sem:
            return await factory()

    tasks = [asyncio.create_task(run_one(f)) for f in coros]
    results = await asyncio.gather(*tasks, return_exceptions=return_exceptions)
    return list(results)  # type: ignore[return-value]
