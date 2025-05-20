from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from pyroute2 import IPRoute
import os
from mac_vendor_lookup import MacLookup
import subprocess

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


def get_connection_method(device_path: Optional[str]) -> Optional[str]:
    if not device_path:
        return None
    if '/usb' in device_path:
        return 'USB'
    if '/pci' in device_path:
        return 'PCIe'
    if '/platform' in device_path:
        return 'Platform'
    return 'Other'


def get_udevadm_info(device_path: Optional[str]) -> Dict[str, Any]:
    if not device_path:
        return {}
    try:
        result = subprocess.run([
            'udevadm', 'info', '--query=property', device_path
        ], capture_output=True, text=True, timeout=2)
        info = {}
        for line in result.stdout.splitlines():
            if '=' in line:
                k, v = line.split('=', 1)
                if k.startswith('ID_'):
                    info[k] = v
        return info
    except Exception:
        return {}


def get_interface_list() -> Dict[str, InterfaceMetadata]:
    """
    Discover all network interfaces and return a dict keyed by system name.
    Each value is an InterfaceMetadata object containing low-level info, manufacturer, connection method, and extra metadata from udevadm.
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
        else:
            device_path = os.path.realpath(device_path)
        # MAC address
        mac_address = attrs.get('IFLA_ADDRESS')
        # Manufacturer
        manufacturer = get_manufacturer(mac_address)
        # Connection method
        connection_method = get_connection_method(device_path)
        # IP addresses
        ip_addresses = []
        idx = link['index']
        for addr in ipr.get_addr(index=idx):
            ip_attrs = dict(addr.get('attrs', []))
            ip = ip_attrs.get('IFA_ADDRESS')
            if ip:
                ip_addresses.append(ip)
        # Extra metadata from udevadm
        extra = get_udevadm_info(device_path)
        interfaces[system_name] = InterfaceMetadata(
            system_name=system_name,
            device_path=device_path,
            mac_address=mac_address,
            ip_addresses=ip_addresses,
            manufacturer=manufacturer,
            connection_method=connection_method,
            extra=extra
        )
    ipr.close()
    return interfaces 