"""
cTrader server endpoints.
"""

# Official cTrader protobuf endpoints
DEMO_HOST = "demo.ctraderapi.com"
LIVE_HOST = "live.ctraderapi.com"
PROTOBUF_PORT = 5035


def get_host(host_type: str) -> str:
    """Get the appropriate host for the given type.
    
    Args:
        host_type: Either "demo" or "live"
        
    Returns:
        Host address
        
    Raises:
        ValueError: If host_type is invalid
    """
    host_type = host_type.lower()
    
    if host_type == "demo":
        return DEMO_HOST
    elif host_type == "live":
        return LIVE_HOST
    else:
        raise ValueError(f"Invalid host_type: {host_type}. Must be 'demo' or 'live'")
