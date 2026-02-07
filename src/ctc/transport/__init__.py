"""
Transport layer for cTrader async client.
"""

from .base import AsyncTransport
from .tcp import TCPTransport
from .protocol import ProtocolFraming
from .endpoints import get_host, DEMO_HOST, LIVE_HOST, PROTOBUF_PORT

# WebSocket transport (optional dependency)
try:
    from .websocket import AsyncWebSocketTransport, websocket_transport
    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False
    AsyncWebSocketTransport = None
    websocket_transport = None

__all__ = [
    "AsyncTransport",
    "TCPTransport",
    "ProtocolFraming",
    "get_host",
    "DEMO_HOST",
    "LIVE_HOST",
    "PROTOBUF_PORT",
    "WEBSOCKET_AVAILABLE",
]

if WEBSOCKET_AVAILABLE:
    __all__.extend(["AsyncWebSocketTransport", "websocket_transport"])
