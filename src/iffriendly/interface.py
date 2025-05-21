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


def classify_device_type(system_name: str, extra: Dict[str, Any]) -> str:
    """
    Classify the device type: WiFi, Ethernet, Bluetooth, Bridge, Tunnel, Loopback, Docker, etc.
    """
    name = system_name.lower()
    if name == 'lo':
        return 'Loopback'
    if name.startswith('wl') or 'wifi' in name or 'wlan' in name:
        return 'WiFi'
    if name.startswith('eth') or name.startswith('en'):
        return 'Ethernet'
    if name.startswith('br'):
        return 'Bridge'
    if name.startswith('docker'):
        return 'Docker Network'
    if name.startswith('veth'):
        return 'Ethernet'
    if name.startswith('tun') or name.startswith('tap'):
        return 'Tunnel'
    if name.startswith('tailscale'):
        return 'Tailscale Network'
    if 'bluetooth' in name or extra.get('ID_BUS') == 'bluetooth':
        return 'Bluetooth'
    return 'Other'


def is_virtual(system_name: str, device_path: Optional[str], device_type: str) -> bool:
    """
    Heuristically determine if the interface is virtual.
    """
    if device_path is None:
        # No physical device path
        if device_type in {'Bridge', 'Docker Network', 'Tunnel', 'Tailscale Network', 'Loopback'}:
            return False  # These are always virtual by nature, but don't need 'Virtual' prefix
        if device_type == 'Ethernet' and (system_name.startswith('veth') or system_name.startswith('ve-')):
            return True
        return True
    return False


def get_interface_list() -> Dict[str, InterfaceMetadata]:
    """
    Discover all network interfaces and return a dict keyed by system name.
    Each value is an InterfaceMetadata object containing low-level info, manufacturer, connection method, extra metadata, and a friendly name.
    Additional enrichers registered via register_enricher() are applied to each interface.
    """
    ipr = IPRoute()
    interfaces = {}
    # First pass: collect all metadata
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
        device_type = classify_device_type(system_name, extra)
        virtual = is_virtual(system_name, device_path, device_type)
        meta = InterfaceMetadata(
            system_name=system_name,
            device_path=device_path,
            mac_address=mac_address,
            ip_addresses=ip_addresses,
            manufacturer=manufacturer,
            connection_method=connection_method,
            friendly_name=None,  # To be filled in second pass
            extra=extra
        )
        # Attach classification for naming
        meta.extra['device_type'] = device_type
        meta.extra['virtual'] = virtual
        meta.extra['internal_external'] = (
            'Internal' if connection_method in ('PCIe', 'Platform') else 'External' if connection_method == 'USB' else None
        )
        interfaces[system_name] = meta
    ipr.close()

    # Second pass: group and generate friendly names
    # Group by (virtual, internal_external, device_type)
    from collections import defaultdict, Counter
    groups = defaultdict(list)
    for meta in interfaces.values():
        key = (
            meta.extra['virtual'],
            meta.extra['internal_external'],
            meta.extra['device_type']
        )
        groups[key].append(meta)

    # For each group, determine if manufacturer or connection type or numbering is needed
    for group in groups.values():
        # Count manufacturers and connection types
        manu_counter = Counter(m.manufacturer for m in group if m.manufacturer)
        conn_counter = Counter(m.connection_method for m in group if m.connection_method)
        # If more than one manufacturer, use manufacturer in name
        manu_needed = len([m for m in group if m.manufacturer]) > 1 and len(set(m.manufacturer for m in group if m.manufacturer)) > 1
        # If more than one connection type, use connection type in name
        conn_needed = len(set(m.connection_method for m in group if m.connection_method)) > 1
        # If more than one device in group, numbering needed
        numbering_needed = len(group) > 1
        # If all manufacturers are None or the same, don't use
        for i, meta in enumerate(group):
            parts = []
            # Virtual prefix only for virtualized physical device types
            if meta.extra['virtual'] and meta.extra['device_type'] in {'Ethernet', 'WiFi', 'Bluetooth'}:
                parts.append('Virtual')
            # Internal/External
            if meta.extra['internal_external']:
                parts.append(meta.extra['internal_external'])
            # Manufacturer
            if manu_needed and meta.manufacturer:
                parts.append(meta.manufacturer)
            # Connection type
            if conn_needed and meta.connection_method:
                parts.append(meta.connection_method)
            # Device type
            parts.append(meta.extra['device_type'])
            # Numbering
            if numbering_needed:
                # Only number if there are otherwise identical names
                base_name = ' '.join(parts)
                # Count how many have the same base name
                base_names = [' '.join([
                    'Virtual' if m.extra['virtual'] and m.extra['device_type'] in {'Ethernet', 'WiFi', 'Bluetooth'} else '',
                    m.extra['internal_external'] or '',
                    m.manufacturer if manu_needed and m.manufacturer else '',
                    m.connection_method if conn_needed and m.connection_method else '',
                    m.extra['device_type']
                ]).strip() for m in group]
                if base_names.count(base_name) > 1:
                    parts.append(f"#{base_names[:i+1].count(base_name)}")
            meta.friendly_name = ' '.join(parts)
            # Fallback: if name is empty, use device type + system_name
            if not meta.friendly_name.strip():
                meta.friendly_name = f"{meta.extra['device_type']} {meta.system_name}"
    # Apply enrichers
    for system_name, meta in interfaces.items():
        for enricher in enrichers:
            updates = enricher(system_name, meta)
            for k, v in updates.items():
                setattr(meta, k, v)
    return interfaces 