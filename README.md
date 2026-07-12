# Toshiba T1200XE Keyboard USB Controller using Raspberry Pi Pico + KMK

## Overview

This project converts the original Toshiba T1200XE laptop keyboard into a modern USB keyboard using a Raspberry Pi Pico (RP2040).

Unlike many modern keyboards, the Toshiba keyboard:

- is a raw keyboard matrix
- has a diode on every key
- uses **active HIGH scanning**
- requires rows to be driven HIGH and columns to use PULL_DOWN inputs

This document describes everything required to reproduce the project from scratch.

---

# Hardware

- Raspberry Pi Pico (RP2040)
- Toshiba T1200XE keyboard
- USB cable
- Soldered connections between keyboard ribbon and Pico GPIO

---

# Software Required

1. CircuitPython
2. CircuitPython Library Bundle
3. adafruit_hid
4. KMK Firmware

---

# IDE Setup (IntelliJ IDEA)

IDEA does not ship with CircuitPython stubs, so `import board`, `import busio`, etc. will show as unresolved by default. Fix:

1. Create a virtual environment in the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install circuitpython-stubs
```

2. Point IDEA to the venv interpreter:
   `File → Project Structure → Project Settings → Project → SDK → open dropdown → Add Python SDK from disk… → Select existing → Python path → select .venv/bin/python`

3. Invalidate caches to force IDEA to index the new stubs:
   `File → Invalidate Caches → Invalidate and Restart`

After restart, `board`, `busio`, `digitalio`, and other CircuitPython modules will resolve correctly.

> Do not install the PyPI package named `board` — it is unrelated to CircuitPython and will not help.

---

# Installing CircuitPython

Download the latest firmware:

https://circuitpython.org/board/raspberry_pi_pico/

Install:

1. Hold BOOTSEL.
2. Connect Pico to USB.
3. Pico appears as

```
RPI-RP2
```

4. Drag the downloaded `.uf2` file onto the drive.

After reboot it appears as

```
CIRCUITPY
```

---

# Connecting to the Serial Console

The Pico exposes a USB serial (CDC) device once CircuitPython is installed. This is how you see `print()` output, KMK debug logs, and the REPL.

## 1. List available tty devices

**macOS:**

```bash
ls /dev/tty.*
```

The Pico shows up as something like `/dev/tty.usbmodem14101`.

**Linux (including Raspberry Pi):**

```bash
ls /dev/ttyACM*
```

The Pico is usually `/dev/ttyACM0` (or the next free number if other USB-serial devices are already connected).

If several devices are listed and you're not sure which one is the Pico, unplug it, re-run the `ls` command, plug it back in, and re-run again — the device that appears is the Pico. On Linux you can also confirm with:

```bash
ls -la /dev/serial/by-id/
```

which prints a descriptive name (e.g. containing `Raspberry_Pi_Pico` or `CircuitPython`) instead of a generic device number.

## 2. Open the serial console with `screen`

```bash
screen /dev/tty.usbmodem14101 115200
```

(substitute the actual device path from step 1; the baud rate `115200` is conventional and CircuitPython ignores it over USB, but you still need to supply a value).

You should land on a blank terminal connected to the board. If `code.py` is running, any `print()` output or KMK debug lines will stream in as they happen. Press Enter if you see nothing — sometimes the first line is swallowed by `screen` attaching mid-output.

## 3. Useful keys once connected

- **Ctrl+D** — soft-reboot: reloads and re-runs `code.py`.
- **Ctrl+C** — interrupt the running program and drop into the REPL.
- **Ctrl+A** then **K**, then **y** — kill the `screen` session (disconnects so another program, like Mu, can open the port).
- **Ctrl+A** then **D** — detach without killing the session (reattach later with `screen -r`).

Only one program can hold the serial port open at a time — if `screen` won't connect, make sure Mu, `tio`, Arduino IDE's serial monitor, etc. aren't already attached to the same device.

---

# Verify CircuitPython

Create `code.py`

```python
print("Hello CircuitPython")
```

Press Ctrl+D in the serial console.

Expected:

```
Hello CircuitPython
```

---

# Install CircuitPython Libraries

Download:

https://circuitpython.org/libraries

Choose the bundle matching your CircuitPython version.

Extract it.

---

# Install adafruit_hid

Copy

```
lib/adafruit_hid
```

from the bundle into

```
CIRCUITPY/lib/
```

Verify:

```python
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode

print("HID installed")
```

---

# Test USB HID

```python
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode

kbd = Keyboard(usb_hid.devices)

kbd.press(Keycode.A)
kbd.release_all()
```

Opening a text editor should automatically type

```
a
```

---

# Install KMK

Download:

https://github.com/KMKfw/kmk_firmware

Copy the folder

```
kmk
```

to

```
CIRCUITPY/
```

Final structure:

```
CIRCUITPY/
│
├── code.py
├── kmk/
└── lib/
    └── adafruit_hid/
```

Verify:

```python
from kmk.keys import KC

print("KMK installed")
```

---

# Toshiba Keyboard Matrix

The Toshiba T1200XE keyboard is

```
8 rows
11 columns
```

Total GPIO required:

```
19
```

---

# GPIO Assignment

Rows

```python
ROWS = [
    board.GP11,
    board.GP12,
    board.GP13,
    board.GP14,
    board.GP20,
    board.GP15,
    board.GP22,
    board.GP21,
]
```

Columns

```python
COLS = [
    board.GP0,
    board.GP1,
    board.GP2,
    board.GP4,
    board.GP3,
    board.GP6,
    board.GP5,
    board.GP7,
    board.GP8,
    board.GP9,
    board.GP10,
]
```

---

# Matrix Polarity

Initially the keyboard was assumed to use the common polarity:

```
Rows LOW
Columns PULL_UP
```

Nothing worked.

Testing revealed that Toshiba uses the opposite polarity.

Correct scan:

```
Rows OUTPUT

inactive = LOW
active = HIGH

Columns INPUT

PULL_DOWN

Pressed key = HIGH
```

This was verified experimentally.

---

# Matrix Scanner

The discovery scanner works like:

```
For every row

    set every row LOW

    drive current row HIGH

    read every column

    if HIGH

        key pressed
```

This scanner was used to build the entire keyboard matrix.

---

# Key Matrix

(The completed matrix mapping goes here.)

Example:

| Row | Col | Key |
|------|------|-----|
|0|0|F1|
|0|1|F2|
|0|2|Esc|
|...|...|...|

---

# KMK Configuration

Example:

```python
import board

from kmk.kmk_keyboard import KMKKeyboard
from kmk.keys import KC
from kmk.scanners import DiodeOrientation

keyboard = KMKKeyboard()

keyboard.row_pins = (
    board.GP11,
    board.GP12,
    board.GP13,
    board.GP14,
    board.GP20,
    board.GP15,
    board.GP22,
    board.GP21,
)

keyboard.col_pins = (
    board.GP0,
    board.GP1,
    board.GP2,
    board.GP4,
    board.GP3,
    board.GP6,
    board.GP5,
    board.GP7,
    board.GP8,
    board.GP9,
    board.GP10,
)

keyboard.diode_orientation = DiodeOrientation.ROW2COL
```

---

# Debounce

Initially

- Enter occasionally generated two presses.
- Shift sometimes failed.

Adding debounce solved the problem.

Example:

```python
from kmk.modules.debounce import Debounce

keyboard.modules.append(Debounce())
```

---

# Disable KMK Debug

If KMK prints

```
kmk.keyboard:
```

messages continuously

disable debugging:

```python
import kmk

kmk.debug_enabled = False
```

---

# Disable CircuitPython REPL

Create `boot.py`

```python
import usb_cdc

usb_cdc.enable(console=False, data=True)
```

This removes the REPL console while keeping a serial data port.

---

# Testing

Test in this order:

- letters
- numbers
- arrows
- Shift
- Ctrl
- Alt
- Enter
- Backspace

---

# Future Improvements

## Fn Key

Implement Toshiba Fn layer using KMK Layers module.

Possible functions:

- brightness
- volume
- overlay keypad
- function remapping

---

## Media Keys

KMK supports:

- Volume Up
- Volume Down
- Mute
- Play
- Pause

---

## Multiple Layers

Possible layers:

Layer 0

Original Toshiba layout

Layer 1

Fn layer

Layer 2

Gaming

Layer 3

Mac layout

---

# Lessons Learned

The most important discovery during reverse engineering was that the Toshiba keyboard **does not use the common active-low scan method**.

Correct operation requires:

```
Rows:
    OUTPUT
    inactive LOW
    active HIGH

Columns:
    INPUT
    PULL_DOWN

Pressed key:
    HIGH
```

This single discovery made the keyboard immediately functional.

---

# Useful Links

CircuitPython

https://circuitpython.org/

CircuitPython Libraries

https://circuitpython.org/libraries

KMK

https://github.com/KMKfw/kmk_firmware

KMK Documentation

https://kmkfw.io

Raspberry Pi Pico

https://www.raspberrypi.com/products/raspberry-pi-pico/

---

Project status:

✅ CircuitPython installed

✅ USB HID working

✅ Keyboard matrix reverse engineered

✅ Active-HIGH polarity discovered

✅ GPIO mapping complete

✅ Key matrix mapped

✅ KMK running

✅ Toshiba keyboard fully functional over USB

## Manually Creating a Wi-Fi Connection with NetworkManager

If the Raspberry Pi detects nearby Wi-Fi networks (`iwlist wlan0 scan` works) but does not have any saved Wi-Fi connections (`nmcli connection show` only lists `lo` and `Wired connection 1`), you can manually create a connection profile.

### 1. Create a new Wi-Fi connection

```bash
sudo nmcli connection add \
    type wifi \
    ifname wlan0 \
    con-name home \
    ssid "az"
```

This creates a new connection profile named **home** for the Wi-Fi network with SSID **az**.

### 2. Configure the security type

```bash
sudo nmcli connection modify home \
    wifi-sec.key-mgmt wpa-psk
```

This tells NetworkManager that the network uses WPA/WPA2 Personal authentication.

### 3. Set the Wi-Fi password

```bash
sudo nmcli connection modify home \
    wifi-sec.psk "12345678"
```

### 4. Activate the connection

```bash
sudo nmcli connection up home
```

If successful, the Raspberry Pi will obtain an IP address from the router.

### 5. Verify the connection

Check the assigned IP address:

```bash
ip addr show wlan0
```

Test Internet connectivity:

```bash
ping -c 4 8.8.8.8
```

Test DNS resolution:

```bash
ping -c 4 google.com
```

### Useful NetworkManager commands

List all saved connections:

```bash
nmcli connection show
```

List network devices:

```bash
nmcli device
```

Show detailed information about the Wi-Fi interface:

```bash
nmcli device show wlan0
```

List nearby Wi-Fi networks:

```bash
nmcli device wifi list
```

Force a Wi-Fi rescan:

```bash
nmcli device wifi rescan
```

Bring the connection up again later:

```bash
sudo nmcli connection up home
```

Disconnect from Wi-Fi:

```bash
sudo nmcli connection down home
```

Delete the connection profile:

```bash
sudo nmcli connection delete home
```