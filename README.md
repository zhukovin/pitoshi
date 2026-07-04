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