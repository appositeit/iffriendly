from iffriendly.interface import get_interface_list, register_enricher

# Example enricher: add a custom field to the 'extra' metadata
def add_custom_field(system_name, meta):
    # You can use any logic here; for demo, add a static field
    return {'extra': {**meta.extra, 'custom_note': f"Custom info for {system_name}"}}

# Register the enricher
register_enricher(add_custom_field)

# Get all interfaces and print their friendly names and custom field
interfaces = get_interface_list()
for name, meta in interfaces.items():
    print(f"{name}: {meta.friendly_name} ({meta.connection_method})")
    print(f"  MAC: {meta.mac_address}")
    print(f"  IPs: {meta.ip_addresses}")
    print(f"  Manufacturer: {meta.manufacturer}")
    print(f"  Device Path: {meta.device_path}")
    print(f"  Extra: {meta.extra}")
    print() 