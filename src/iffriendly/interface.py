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

Example usage:
    from iffriendly.interface import get_interface_list, register_enricher

    # Register a custom enricher
    def add_custom_field(system_name, meta):
        return {'extra': {**meta.extra, 'custom': 'value'}}
    register_enricher(add_custom_field)

    # Get all interfaces
    interfaces = get_interface_list()
    for name, meta in interfaces.items():
        print(f"{name}: {meta.friendly_name} ({meta.connection_method})")
"""

class InterfaceMetadata(BaseModel):
    """
    Data model for network interface metadata.
    """
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
    """
    Register a metadata enrichment function.
    The function should take (system_name, meta: InterfaceMetadata) and return a dict of updates.
    """
    enrichers.append(func)


def get_manufacturer(mac: Optional[str]) -> Optional[str]:
    """
    Look up the manufacturer for a given MAC address using mac-vendor-lookup.
    Returns the manufacturer name or None if not found.
    """
    if not mac:
        return None
    try:
        return MacLookup().lookup(mac)
    except Exception:
        return None


def get_connection_method(device_path: Optional[str]) -> Optional[str]:
    """
    Heuristically determine the connection method (USB, PCIe, Platform, Other) from the device path.
    """
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
    """
    Collect additional metadata from udevadm for the given device path.
    Returns a dict of ID_* fields.
    """
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
    """
    Generate a human-friendly name for the interface using available metadata.
    """
    model = extra.get('ID_MODEL', '')
    vendor = extra.get('ID_VENDOR', '')
    bus = extra.get('ID_BUS', '')
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
    if 'bluetooth' in system_name or bus == 'bluetooth':
        if manufacturer:
            return f"{manufacturer} Bluetooth Adapter"
        return "Bluetooth Adapter"
    if 'rndis' in system_name or 'usb' in system_name:
        if vendor and model:
            return f"USB tethered {vendor} {model}"
        if manufacturer:
            return f"USB tethered {manufacturer} device"
        return "USB tethered device"
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
        device_path = f"/sys/class/net/{system_name}/device"
        if not os.path.exists(device_path):
            device_path = None
        else:
            device_path = os.path.realpath(device_path)
        mac_address = attrs.get('IFLA_ADDRESS')
        manufacturer = get_manufacturer(mac_address)
        connection_method = get_connection_method(device_path)
        ip_addresses = []
        idx = link['index']
        for addr in ipr.get_addr(index=idx):
            ip_attrs = dict(addr.get('attrs', []))
            ip = ip_attrs.get('IFA_ADDRESS')
            if ip:
                ip_addresses.append(ip)
        extra = get_udevadm_info(device_path)
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