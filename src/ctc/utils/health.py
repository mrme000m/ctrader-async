"""Connection health monitoring utilities.

Provides health status snapshots for monitoring connection quality.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..client import CTraderClient
    from .metrics import MetricsCollector, MetricsSnapshot


@dataclass
class HealthStatus:
    """Connection health snapshot.
    
    Attributes:
        connected: Whether client is connected
        authenticated: Whether client is authenticated
        latency_ms: Average request latency in milliseconds (None if no data)
        last_inbound_age_s: Seconds since last inbound message
        reconnect_attempts: Number of reconnect attempts
        metrics: Full metrics snapshot
        healthy: Overall health assessment
    """
    connected: bool
    authenticated: bool
    latency_ms: Optional[float]
    last_inbound_age_s: float
    reconnect_attempts: int
    metrics: "MetricsSnapshot"
    
    @property
    def healthy(self) -> bool:
        """Overall health assessment."""
        if not self.connected or not self.authenticated:
            return False
        if self.last_inbound_age_s > 120:  # 2 minutes without data
            return False
        if self.latency_ms is not None and self.latency_ms > 5000:  # >5s latency
            return False
        return True
    
    def __repr__(self) -> str:
        status = "HEALTHY" if self.healthy else "UNHEALTHY"
        return (
            f"<HealthStatus {status} "
            f"connected={self.connected} "
            f"auth={self.authenticated} "
            f"latency={self.latency_ms:.1f}ms "
            f"idle={self.last_inbound_age_s:.1f}s>"
        )


async def get_health(
    client: "CTraderClient",
    metrics: Optional["MetricsCollector"] = None,
) -> HealthStatus:
    """Get connection health snapshot.
    
    Args:
        client: CTrader client instance
        metrics: Optional metrics collector for latency/reconnect data
        
    Returns:
        HealthStatus with current connection health
        
    Example:
        >>> health = await get_health(client, client.metrics)
        >>> if health.healthy:
        ...     print(f"Connection healthy, latency: {health.latency_ms:.1f}ms")
        ... else:
        ...     print(f"Connection issues detected")
    """
    # Get connection state
    connected = getattr(client, '_connected', False)
    authenticated = getattr(client, '_authenticated', False)
    
    # Get last inbound time
    last_inbound = getattr(client, '_last_inbound_monotonic', None)
    if last_inbound:
        last_inbound_age_s = time.monotonic() - last_inbound
    else:
        last_inbound_age_s = float('inf')
    
    # Get metrics snapshot
    if metrics:
        snapshot = metrics.snapshot()
        latency_ms = snapshot.avg_latency * 1000.0 if snapshot.avg_latency else None
        reconnect_attempts = snapshot.reconnect_attempts
    else:
        snapshot = None
        latency_ms = None
        reconnect_attempts = 0
    
    return HealthStatus(
        connected=connected,
        authenticated=authenticated,
        latency_ms=latency_ms,
        last_inbound_age_s=last_inbound_age_s,
        reconnect_attempts=reconnect_attempts,
        metrics=snapshot,
    )
