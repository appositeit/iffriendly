from iffriendly.interface import get_interface_list

interfaces = get_interface_list()
for name, meta in interfaces.items():
    print(f"{name}: {meta.friendly_name} ({meta.connection_method})")
    print(f"  MAC: {meta.mac_address}")
    print(f"  IPs: {meta.ip_addresses}")
    print(f"  Manufacturer: {meta.manufacturer}")
    print(f"  Device Path: {meta.device_path}")
    print(f"  Extra: {meta.extra}")
    print()

for name, meta in interfaces.items():
    print(f"{name}: {meta.friendly_name}")
