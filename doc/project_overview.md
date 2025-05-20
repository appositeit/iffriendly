# Project Overview: iffriendly

## Purpose

The `iffriendly` library is a Python library designed to provide human-friendly names and rich metadata for network interfaces on Linux systems. Its goal is to make network interface information accessible and understandable for both developers and end-users, enabling better diagnostics, UI/UX, and automation.

## Key Features

- **Interface Discovery:** Enumerate all network interfaces on a system.
- **Rich Metadata:** For each interface, provide:
  - System name (e.g., `eth0`, `wlan0`)
  - Device path
  - MAC address
  - IP address(es)
  - Manufacturer information (via OUI lookup)
  - Connection method (e.g., internal PCIe, internal USB, external USB, Bluetooth, tethered phone)
  - Heuristically generated, human-friendly name (e.g., "Internal WiFi", "Broadcom WiFi dongle", "USB tethered Samsung Mobile Phone")
- **Extensible:** Designed to support additional metadata sources and heuristics.
- **Integration Ready:** Output is a dictionary suitable for use in UI components (e.g., JS hovercards).

## Heuristics and Data Sources

- Uses Linux system paths (e.g., `/sys/class/net/<iface>/device`) to distinguish between internal and external devices.
- Integrates with tools like `udevadm`, `lsusb`, and `lspci` for bus and device information.
- Uses OUI MAC address lookup for manufacturer data.

## Intended Directory Structure

- `src/`: Source code for the library
- `tests/`: Unit and integration tests
- `doc/`: Project documentation
  - `doc/progress/`: Progress updates
- `bin/`: Scripts and tools
- `logs/`: Log files (should be in `.gitignore`)
- `tools/`: Development tools/scripts
- `config/`: Configuration files and templates

## Development Principles

- Modular, extensible codebase
- Automated testing (unit, API, E2E)
- High test coverage (aim for 80%+)
- Use of Pydantic for type safety
- Progress tracked via timestamped updates in `doc/progress/`
- Version control with Git, using branches for major changes
- Wrapper scripts for recurring processes
- Clear, up-to-date documentation

## Next Steps

- Implementation plan (see `doc/implementation_plan.md`)
- Initial library scaffolding and core function (`get_interface_list`)
- Unit tests for all modules
- Progress updates and documentation

## Extensibility and Custom Metadata Enrichers

The `iffriendly` library is designed to be extensible. You can add custom metadata enrichment logic by registering additional enrichment functions using `register_enricher`. Each enricher is called with `(system_name, meta: InterfaceMetadata)` and should return a dict of updates to apply to the interface metadata.

**Example:**

```python
from iffriendly.interface import get_interface_list, register_enricher

def add_custom_field(system_name, meta):
    return {'extra': {**meta.extra, 'custom': 'value'}}
register_enricher(add_custom_field)

interfaces = get_interface_list()
for name, meta in interfaces.items():
    print(f"{name}: {meta.friendly_name} ({meta.connection_method})")
```

This allows you to easily extend the metadata available for each interface, integrate with new data sources, or add custom heuristics for your environment. 