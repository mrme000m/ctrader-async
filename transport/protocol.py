"""
Protocol framing and message encoding/decoding.
"""

from __future__ import annotations

import logging
from typing import Optional, Any

from google.protobuf.message import Message

logger = logging.getLogger(__name__)


class ProtocolFraming:
    """Handle cTrader protobuf message framing.
    
    The cTrader protocol wraps protobuf messages in a ProtoMessage envelope
    with a 4-byte big-endian length prefix.
    
    Message structure:
        [4 bytes: length][ProtoMessage: payloadType, payload, clientMsgId]
    """
    
    @staticmethod
    def encode(
        message: Message,
        client_msg_id: Optional[str] = None
    ) -> bytes:
        """Encode a protobuf message with length prefix.
        
        Args:
            message: Protobuf message to encode
            client_msg_id: Optional client message ID for correlation
            
        Returns:
            Encoded bytes ready to send (length prefix + ProtoMessage)
            
        Example:
            >>> req = ProtoOAApplicationAuthReq()
            >>> req.clientId = "12345"
            >>> data = ProtocolFraming.encode(req, client_msg_id="msg-001")
            >>> await transport.send(data)
        """
        try:
            # Import here to avoid circular dependency
            from ..messages.OpenApiCommonMessages_pb2 import ProtoMessage
            from ..protobuf import Protobuf
            
            # Create ProtoMessage envelope
            proto_msg = ProtoMessage()
            
            # Set payload type.
            # In cTrader pb2 messages, most request/response classes expose a `payloadType` attribute.
            # Most request/response classes expose a `payloadType` attribute.
            # If not, we fall back to resolving by class name via our local Protobuf registry.
            payload_type = getattr(message, "payloadType", None)
            if payload_type is None:
                # Fallback: derive by class name via Protobuf registry
                payload_type = Protobuf.get_type(type(message).__name__)
            proto_msg.payloadType = int(payload_type)
            
            # Serialize inner message as payload
            proto_msg.payload = message.SerializeToString()
            
            # Add client message ID if provided
            if client_msg_id:
                proto_msg.clientMsgId = client_msg_id
            
            # Serialize the ProtoMessage
            serialized = proto_msg.SerializeToString()
            
            # Add 4-byte length prefix (big-endian)
            length = len(serialized)
            length_bytes = length.to_bytes(4, byteorder='big', signed=False)
            
            logger.debug(
                f"Encoded message: type={proto_msg.payloadType}, "
                f"size={length}, clientMsgId={client_msg_id}"
            )
            
            return length_bytes + serialized
            
        except Exception as e:
            logger.error(f"Failed to encode message: {e}")
            raise
    
    @staticmethod
    def decode(data: bytes) -> Any:
        """Decode a protobuf message (without length prefix).
        
        Args:
            data: Raw message bytes (ProtoMessage, without length prefix)
            
        Returns:
            ProtoMessage object
            
        Example:
            >>> async for message_bytes in transport.receive():
            ...     proto_msg = ProtocolFraming.decode(message_bytes)
            ...     print(f"Received: {proto_msg.payloadType}")
        """
        try:
            from ..messages.OpenApiCommonMessages_pb2 import ProtoMessage
            
            proto_msg = ProtoMessage()
            proto_msg.ParseFromString(data)
            
            logger.debug(
                f"Decoded message: type={proto_msg.payloadType}, "
                f"clientMsgId={proto_msg.clientMsgId if proto_msg.HasField('clientMsgId') else None}"
            )
            
            return proto_msg
            
        except Exception as e:
            logger.error(f"Failed to decode message: {e}")
            raise
    
    @staticmethod
    def extract_payload(proto_msg: Any) -> Message:
        """Extract the inner payload from a ProtoMessage.
        
        Args:
            proto_msg: ProtoMessage envelope
            
        Returns:
            Extracted inner protobuf message
            
        Example:
            >>> proto_msg = ProtocolFraming.decode(message_bytes)
            >>> inner_msg = ProtocolFraming.extract_payload(proto_msg)
            >>> if isinstance(inner_msg, ProtoOATraderRes):
            ...     print(f"Balance: {inner_msg.trader.balance}")
        """
        try:
            from ..protobuf import Protobuf
            return Protobuf.extract(proto_msg)
        except Exception as e:
            logger.error(f"Failed to extract payload: {e}")
            raise
    
    @staticmethod
    def get_payload_type(message: Message) -> int:
        """Get the payload type ID for a message.
        
        Args:
            message: Protobuf message
            
        Returns:
            Payload type integer
        """
        try:
            from ..protobuf import Protobuf
            payload_type = getattr(message, "payloadType", None)
            if payload_type is None:
                payload_type = Protobuf.get_type(type(message).__name__)
            return int(payload_type)
        except Exception as e:
            logger.error(f"Failed to get payload type: {e}")
            raise
