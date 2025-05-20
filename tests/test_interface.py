import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

import pytest
from src.iffriendly.interface import get_interface_list, InterfaceMetadata, get_manufacturer, register_enricher

def test_get_interface_list_not_implemented():
    # This test is now obsolete, but kept for reference
    pass

def test_interface_metadata_instantiation():
    data = {
        'system_name': 'eth0',
        'device_path': '/sys/class/net/eth0/device',
        'mac_address': '00:11:22:33:44:55',
        'ip_addresses': ['192.168.1.2'],
        'manufacturer': 'Intel',
        'connection_method': 'PCIe',
        'friendly_name': 'Internal Ethernet',
        'extra': {'speed': '1Gbps'}
    }
    iface = InterfaceMetadata(**data)
    assert iface.system_name == 'eth0'
    assert iface.friendly_name == 'Internal Ethernet'
    assert iface.extra['speed'] == '1Gbps'

def test_get_interface_list_basic():
    interfaces = get_interface_list()
    assert isinstance(interfaces, dict)
    # There should be at least one interface (lo is always present on Linux)
    assert interfaces, 'No interfaces found.'
    for name, meta in interfaces.items():
        assert isinstance(meta, InterfaceMetadata)
        assert meta.system_name == name
        # MAC address may be None for loopback, but should be a string or None
        assert meta.mac_address is None or isinstance(meta.mac_address, str)
        assert isinstance(meta.ip_addresses, list)

def test_manufacturer_lookup():
    # Test that manufacturer lookup does not raise and returns a string or None
    interfaces = get_interface_list()
    for meta in interfaces.values():
        if meta.mac_address and meta.mac_address != '00:00:00:00:00:00':
            manufacturer = get_manufacturer(meta.mac_address)
            assert manufacturer is None or isinstance(manufacturer, str)

def test_connection_method_heuristics():
    interfaces = get_interface_list()
    valid_methods = {None, 'USB', 'PCIe', 'Platform', 'Other'}
    for meta in interfaces.values():
        assert meta.connection_method in valid_methods

def test_udevadm_extra_metadata():
    interfaces = get_interface_list()
    for meta in interfaces.values():
        assert isinstance(meta.extra, dict)
        if meta.extra:
            for k in meta.extra.keys():
                assert k.startswith('ID_')

def test_friendly_name_generation():
    interfaces = get_interface_list()
    for name, meta in interfaces.items():
        assert isinstance(meta.friendly_name, str)
        assert meta.friendly_name
        # If we have manufacturer, model, or connection method, friendly_name should not just be the system name
        if meta.manufacturer or meta.connection_method or meta.extra.get('ID_MODEL'):
            assert meta.friendly_name != name

def test_register_enricher():
    # Register a dummy enricher that adds a custom field
    def dummy_enricher(system_name, meta):
        return {'extra': {**meta.extra, 'dummy_field': 'dummy_value'}}
    register_enricher(dummy_enricher)
    interfaces = get_interface_list()
    for meta in interfaces.values():
        assert 'dummy_field' in meta.extra and meta.extra['dummy_field'] == 'dummy_value' 