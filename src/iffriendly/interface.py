from typing import Dict, Any, List, Optional, Callable
from pydantic import BaseModel
from pyroute2 import IPRoute
import os
from mac_vendor_lookup import MacLookup
import subprocess

"""
iffriendly.interface

This module provides the core interface discovery and metadata enrichment logic.

Extensibility:
- Additional metadata enrichment functions can be registered via register_enricher().
- Each enricher is called with (system_name, meta: InterfaceMetadata) and should return a dict of updates to apply to the InterfaceMetadata.
"""

class InterfaceMetadata(BaseModel):
    system_name: str
    device_path: Optional[str] = None
    mac_address: Optional[str] = None
    ip_addresses: List[str] = []
    manufacturer: Optional[str] = None
    connection_method: Optional[str] = None
    friendly_name: Optional[str] = None
    extra: Dict[str, Any] = {}

# List of enrichment functions
enrichers: List[Callable[[str, InterfaceMetadata], Dict[str, Any]]] = []

def register_enricher(func: Callable[[str, InterfaceMetadata], Dict[str, Any]]):
    enrichers.append(func)


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


def generate_friendly_name(system_name: str, manufacturer: Optional[str], connection_method: Optional[str], extra: Dict[str, Any]) -> str:
    # Prefer descriptive names based on connection, manufacturer, and model
    model = extra.get('ID_MODEL', '')
    vendor = extra.get('ID_VENDOR', '')
    bus = extra.get('ID_BUS', '')
    # WiFi
    if 'wlan' in system_name or 'wifi' in system_name.lower():
        if connection_method == 'USB':
            if manufacturer:
                return f"{manufacturer} USB WiFi Adapter"
            return "USB WiFi Adapter"
        if connection_method == 'PCIe':
            if manufacturer:
                return f"Internal {manufacturer} WiFi"
            return "Internal WiFi"
        return "WiFi Adapter"
    # Ethernet
    if 'eth' in system_name or 'en' in system_name:
        if connection_method == 'USB':
            if manufacturer:
                return f"{manufacturer} USB Ethernet Adapter"
            return "USB Ethernet Adapter"
        if connection_method == 'PCIe':
            if manufacturer:
                return f"Internal {manufacturer} Ethernet"
            return "Internal Ethernet"
        return "Ethernet Adapter"
    # Bluetooth
    if 'bluetooth' in system_name or bus == 'bluetooth':
        if manufacturer:
            return f"{manufacturer} Bluetooth Adapter"
        return "Bluetooth Adapter"
    # Tethered phone
    if 'rndis' in system_name or 'usb' in system_name:
        if vendor and model:
            return f"USB tethered {vendor} {model}"
        if manufacturer:
            return f"USB tethered {manufacturer} device"
        return "USB tethered device"
    # Fallbacks
    if manufacturer and model:
        return f"{manufacturer} {model} ({system_name})"
    if manufacturer:
        return f"{manufacturer} device ({system_name})"
    if model:
        return f"{model} ({system_name})"
    return system_name


def get_interface_list() -> Dict[str, InterfaceMetadata]:
    """
    Discover all network interfaces and return a dict keyed by system name.
    Each value is an InterfaceMetadata object containing low-level info, manufacturer, connection method, extra metadata, and a friendly name.
    Additional enrichers registered via register_enricher() are applied to each interface.
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
        # Friendly name
        friendly_name = generate_friendly_name(system_name, manufacturer, connection_method, extra)
        meta = InterfaceMetadata(
            system_name=system_name,
            device_path=device_path,
            mac_address=mac_address,
            ip_addresses=ip_addresses,
            manufacturer=manufacturer,
            connection_method=connection_method,
            friendly_name=friendly_name,
            extra=extra
        )
        # Apply enrichers
        for enricher in enrichers:
            updates = enricher(system_name, meta)
            for k, v in updates.items():
                setattr(meta, k, v)
        interfaces[system_name] = meta
    ipr.close()
    return interfaces 