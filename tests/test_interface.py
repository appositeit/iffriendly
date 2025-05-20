import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

import pytest
from src.iffriendly.interface import get_interface_list, InterfaceMetadata

def test_get_interface_list_not_implemented():
    with pytest.raises(NotImplementedError):
        get_interface_list()

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