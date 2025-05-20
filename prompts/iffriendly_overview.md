# iffriendly overview

The iffriendly library will be a python library that provides human friendly names for network interfaces.

Let's start by focusing on the library. I think the key function should be get_interface_list and it returns a dict keyed by the if name/system name and value is a dict of other information. That sub dict contains a low level information (device path, mac address, IP address), manufacturer information (i available), metadata such as a connection method (internal PCIe, internal USB, external USB, etc- see below) and finally a unique heuristically generated friendly human readable name ("Internal WiFi", "Broadcom WiFi dongle", "USB tethered Samsung Mobile Phone", "Bluetooth tethered Pixel Phone").

Once we have the library we might build a standard js library that builds a hovercard given the device dict.

## Making the best fucking hovercards!
Let's spend some time making a really good "interface" library. If we start with something like the python pyroute2 library we can get a lot of fundamental information. We can use the OUI MAC address information from the mac-vendor-lookup package to get manufacturer information. 

How do we know if this is an internal or external device?

You can distinguish **built-in vs external** (e.g., USB dongles) network devices in Linux by inspecting the **device's location in the system device tree**, primarily under `/sys/class/net/<iface>/device` or `/sys/class/bluetooth/hciX/device`. Here's how:

### ✅ **Key heuristics to distinguish built-in vs external**

#### 🔍 **1. Check if it's connected via USB**

If the path under `/sys/class/net/<iface>/device` or `/sys/class/bluetooth/hciX/device` contains `/usb`, it's an external USB device.

**Example:**

```bash
realpath /sys/class/net/wlan0/device
# /sys/devices/pci0000:00/0000:00:14.0/usb1/1-1/1-1.3/1-1.3:1.0/net/wlan0 → USB
```

Built-in devices usually appear directly under PCI or platform buses:

```bash
realpath /sys/class/net/eth0/device
# /sys/devices/pci0000:00/0000:00:1f.6 → Built-in (PCI)
```

#### 🧪 Python way:

```python
import os

def is_usb_device(interface):
    device_path = os.path.realpath(f"/sys/class/net/{interface}/device")
    return "/usb" in device_path

print("wlan0 is USB:", is_usb_device("wlan0"))
```

For Bluetooth:

```python
def is_usb_bluetooth(hci):
    device_path = os.path.realpath(f"/sys/class/bluetooth/{hci}/device")
    return "/usb" in device_path
```

---

### 🖥️ Other metadata

* **`udevadm info`** can give detailed bus info:

  ```bash
  udevadm info /sys/class/net/wlan0 | grep ID_BUS
  # ID_BUS=usb → External
  ```
* **`lsusb` / `lspci`** output may help if you want to build a UI or label devices.

---

### 🧠 Summary

| Check Method                           | Built-in                          | USB (External)          |
| -------------------------------------- | --------------------------------- | ----------------------- |
| `/sys/.../device` path                 | `/pci...` or `/platform...`       | contains `/usb`         |
| `udevadm info` → `ID_BUS`              | Not present or `pci`              | `usb`                   |
| `ls -l /sys/class/net/*/device/driver` | Usually `e1000e`, `iwlwifi`, etc. | Often `rtl88xxau`, etc. |

The project directory for this work here:

/home/jem/development/iffriendly

[[project_maintenance_rules]]

Start by writing this content out as a project overview in the doc directory.

Then write an implementation plan. The implementation plan should consider planning, development, testing approaches as well as the feature implementation process. Make sure sections/subsctions are
numbered for easy reference e.g. "2.1.3 Feature Implemenation Detail". In progress reports reference
which part of the implementation plan has been addressed. Update the implementation plan with progress
so we know where we are up to.