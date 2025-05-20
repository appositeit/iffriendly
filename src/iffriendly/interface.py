from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from pyroute2 import IPRoute
import os
from mac_vendor_lookup import MacLookup

class InterfaceMetadata(BaseModel):
    system_name: str
    device_path: Optional[str] = None
    mac_address: Optional[str] = None
    ip_addresses: List[str] = []
    manufacturer: Optional[str] = None
    connection_method: Optional[str] = None
    friendly_name: Optional[str] = None
    extra: Dict[str, Any] = {}


def get_manufacturer(mac: Optional[str]) -> Optional[str]:
    if not mac:
        return None
    try:
        return MacLookup().lookup(mac)
    except Exception:
        return None


def get_interface_list() -> Dict[str, InterfaceMetadata]:
    """
    Discover all network interfaces and return a dict keyed by system name.
    Each value is an InterfaceMetadata object containing low-level info and manufacturer.
    """
    ipr = IPRoute()
    interfaces = {}
    for link in ipr.get_links():
        attrs = dict(link.get('attrs', []))
        system_name = attrs.get('IFLA_IFNAME')
        if not system_name:
            continue
        # Device path
        device_path = f"/sys/class/net/{system_name}/device"
        if not os.path.exists(device_path):
            device_path = None
        # MAC address
        mac_address = attrs.get('IFLA_ADDRESS')
        # Manufacturer
        manufacturer = get_manufacturer(mac_address)
        # IP addresses
        ip_addresses = []
        idx = link['index']
        for addr in ipr.get_addr(index=idx):
            ip_attrs = dict(addr.get('attrs', []))
            ip = ip_attrs.get('IFA_ADDRESS')
            if ip:
                ip_addresses.append(ip)
        interfaces[system_name] = InterfaceMetadata(
            system_name=system_name,
            device_path=device_path,
            mac_address=mac_address,
            ip_addresses=ip_addresses,
            manufacturer=manufacturer
        )
    ipr.close()
    return interfaces 