"""
Protocol layer for message correlation and dispatch.
"""

from .correlation import RequestCorrelator
from .dispatcher import MessageDispatcher
from .handler import ProtocolHandler

__all__ = [
    "RequestCorrelator",
    "MessageDispatcher",
    "ProtocolHandler",
]
