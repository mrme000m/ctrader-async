"""Local Protobuf registry helper.

This is a small, dependency-free port of the upstream `ctrader_open_api.protobuf.Protobuf`
helper. It allows mapping between payloadType integers and the generated protobuf
message classes.

We vendor this to avoid depending on the upstream `ctrader-open-api` package (Twisted).
"""

from __future__ import annotations

import re
from typing import Any, Dict, Type


class Protobuf:
    """Registry for mapping `payloadType` -> protobuf class and back."""

    _protos: Dict[int, Type[Any]] = {}
    _names: Dict[str, int] = {}
    _abbr_names: Dict[str, int] = {}

    @classmethod
    def populate(cls) -> Dict[int, Type[Any]]:
        from . import messages as _messages

        # Import both files (Common + OA)
        modules = [
            _messages.OpenApiCommonMessages_pb2,
            _messages.OpenApiMessages_pb2,
        ]

        for m in modules:
            for name in dir(m):
                if not name.startswith("Proto"):
                    continue

                klass = getattr(m, name)

                # Only process protobuf message classes
                try:
                    inst = klass()
                except Exception:
                    continue

                payload_type = getattr(inst, "payloadType", None)
                if payload_type is None:
                    continue

                cls._protos[int(payload_type)] = klass
                cls._names[klass.__name__] = int(payload_type)

                abbr_name = re.sub(r"^Proto(OA)?(.*)", r"\2", klass.__name__)
                cls._names[abbr_name] = int(payload_type)

        return cls._protos

    @classmethod
    def get(cls, payload: int | str, fail: bool = True, **params: Any) -> Any:
        if not cls._protos:
            cls.populate()

        if isinstance(payload, int) and payload in cls._protos:
            return cls._protos[payload](**params)

        # Resolve name -> type
        for d in (cls._names, cls._abbr_names):
            if isinstance(payload, str) and payload in d:
                payload_type = d[payload]
                return cls._protos[payload_type](**params)

        if fail:
            raise IndexError(f"Invalid payload: {payload}")
        return None

    @classmethod
    def get_type(cls, payload: int | str, **params: Any) -> int:
        p = cls.get(payload, **params)
        return int(p.payloadType)

    @classmethod
    def extract(cls, message: Any) -> Any:
        payload = cls.get(int(message.payloadType))
        payload.ParseFromString(message.payload)
        return payload
