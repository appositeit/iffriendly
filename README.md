# iffriendly

A Python library for providing human-friendly names and rich metadata for network interfaces on Linux systems.

## Features

- Discover all network interfaces on a Linux system
- Get rich metadata for each interface:
  - System name (e.g., `eth0`, `wlan0`)
  - Device path
  - MAC address and manufacturer
  - IP addresses
  - Connection method (PCIe, USB, Platform, etc.)
  - Human-friendly name (e.g., "Internal Intel WiFi", "USB Ethernet Adapter")
- Extensible metadata enrichment system
- Integration-ready output format

## Requirements

- Linux operating system
- Python 3.8 or later
- Root access (for some features)

## Installation

```bash
pip install iffriendly
```

For development:

```bash
pip install iffriendly[dev]
```

## Usage

Basic usage:

```python
from iffriendly.interface import get_interface_list

# Get all interfaces with metadata
interfaces = get_interface_list()

# Print friendly names and connection methods
for name, meta in interfaces.items():
    print(f"{name}: {meta.friendly_name} ({meta.connection_method})")
```

Adding custom metadata:

```python
from iffriendly.interface import register_enricher, get_interface_list

# Register a custom metadata enricher
def add_custom_field(system_name, meta):
    return {'extra': {**meta.extra, 'custom': 'value'}}
register_enricher(add_custom_field)

# Get enriched interface data
interfaces = get_interface_list()
```

## Development

1. Clone the repository:
```bash
git clone https://github.com/jem/iffriendly.git
cd iffriendly
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Linux/macOS
```

3. Install development dependencies:
```bash
pip install -e ".[dev]"
```

4. Run tests:
```bash
pytest
```

## License

Apache License 2.0. See the LICENSE file for details. 