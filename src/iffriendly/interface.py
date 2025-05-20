from typing import Dict, Any, List, Optional
from pydantic import BaseModel

class InterfaceMetadata(BaseModel):
    system_name: str
    device_path: Optional[str] = None
    mac_address: Optional[str] = None
    ip_addresses: List[str] = []
    manufacturer: Optional[str] = None
    connection_method: Optional[str] = None
    friendly_name: Optional[str] = None
    extra: Dict[str, Any] = {}


def get_interface_list() -> Dict[str, InterfaceMetadata]:
    """
    Discover all network interfaces and return a dict keyed by system name.
    Each value is an InterfaceMetadata object containing low-level info, manufacturer,
    connection method, and a heuristically generated friendly name.
    """
    raise NotImplementedError("Interface discovery not yet implemented.") 