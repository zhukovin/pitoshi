"""
Free-form ghost-key diagnostic for the Toshiba T1200XE matrix.

Unlike ghost_key_test.py (which walks a fixed list of keys one at a time),
this one just listens. Press whatever keys you like, in whatever order,
repeating each one a random number of times (more than once) before moving
to the next. Anytime a key shows up while some other key is still being
held down - which should never happen if you're only pressing one key at a
time - that's a hardware ghost, and it gets flagged.

Talks straight to CircuitPython's keypad.KeyMatrix, bypassing KMK entirely,
so nothing gets typed anywhere - results only go to the serial console.

Usage:
  1. Back up the real CIRCUITPY/code.py, then copy this file over it.
  2. Open the serial console (see README: "Connecting to the Serial Console").
  3. Press Ctrl+D to (re)run it if it doesn't start automatically.
  4. Mash away. Press a key a handful of times, switch to another, repeat.
  5. Ctrl+C stops it.
  6. When done, copy the original code.py back.
"""

import time

import board
import keypad

# Must match code.py's matrix wiring exactly.
ROW_PINS = (
    board.GP11, board.GP12, board.GP13, board.GP14,
    board.GP20, board.GP15, board.GP22, board.GP21,
)
COL_PINS = (
    board.GP0, board.GP1, board.GP2, board.GP4,
    board.GP3, board.GP6, board.GP5, board.GP7,
    board.GP8, board.GP9, board.GP10,
)
NUM_COLS = len(COL_PINS)

# key_number -> label, row-major, matching code.py's layer-0 keymap.
LABELS = [
    'F1', 'F2', 'ESC', 'N2', 'N4', 'N6', 'N8', 'N0', 'EQL', 'BSPC', 'PAUS',
    'F11', 'F12', 'N1', 'N3', 'N5', 'N7', 'N9', 'MINS', 'UP', 'DOWN', 'FN',
    'F3', 'F4', 'TAB', 'W', 'R', 'Y', 'I', 'P', 'LBRC', 'HOME', '--',
    'PGDN', 'PGUP', 'Q', 'E', 'T', 'U', 'O', 'LEFT', 'RBRC', 'ENT', '--',
    'F5', 'F6', 'A', 'S', 'F', 'H', 'J', 'L', 'RIGHT', 'GRV', '--',
    'F7', 'F8', 'LCTL', 'D', 'G', 'B', 'K', 'SCLN', 'QUOT', 'RSFT', '--',
    'F9', 'F10', 'LSFT', 'Z', 'V', 'N', 'COMM', 'DOT', 'SLSH', 'PSCR', '--',
    'END', 'LALT', 'BSLS', 'X', 'C', 'SPC', 'M', 'DEL', 'CAPS', 'INS', '--',
]


def label(number):
    if 0 <= number < len(LABELS):
        return LABELS[number]
    return 'UNKNOWN(%d)' % number


BUFFER_SIZE = 12          # how many recent presses to show around an anomaly
IDLE_FLUSH_SECONDS = 1.0  # report a pending anomaly once presses pause

LETTERS = 'abcdefghijklmnopqrstuvwxyz'

RED = '\033[31m'
RESET = '\033[0m'

matrix = keypad.KeyMatrix(
    row_pins=ROW_PINS,
    column_pins=COL_PINS,
    columns_to_anodes=False,  # matches DiodeOrientation.ROW2COL in code.py
    interval=0.002,
    debounce_threshold=15,
)


def main():
    print()
    print('Pattern anomaly diagnostic. Press keys in any order, repeating')
    print('each one a few times before switching. Ctrl+C to stop.')
    print()

    held = set()
    letter_for = {}     # key_number -> assigned single letter
    next_letter = 0
    buffer = []          # list of (letter, key_number) for recent presses
    pending = False      # an anomaly is waiting to be reported
    last_event_time = time.monotonic()

    current_key = None  # key_number the progress line is currently counting
    current_count = 0

    def print_progress():
        print('\r%s x%d ' % (label(current_key), current_count), end='')

    try:
        while True:
            ev = matrix.events.get()

            if ev is None:
                if pending and (time.monotonic() - last_event_time) >= IDLE_FLUSH_SECONDS:
                    if current_key is not None:
                        print()  # close out the in-progress counter line
                    pattern = ''.join(letter for letter, _ in buffer)
                    legend = ', '.join(
                        '%s=%s' % (letter, label(kn))
                        for letter, kn in sorted(set(buffer), key=lambda t: t[0])
                    )
                    print('%s!! I saw this pattern "%s" - is that intended?%s' % (RED, pattern, RESET))
                    print('   %s' % legend)
                    pending = False
                    if current_key is not None:
                        print_progress()  # resume the counter line
                time.sleep(0.001)
                continue

            last_event_time = time.monotonic()
            kn = ev.key_number

            if ev.pressed:
                if kn not in letter_for:
                    letter_for[kn] = LETTERS[next_letter % len(LETTERS)]
                    next_letter += 1
                buffer.append((letter_for[kn], kn))
                buffer = buffer[-BUFFER_SIZE:]

                is_ghost = bool(held)
                if is_ghost:
                    pending = True
                else:
                    if kn != current_key:
                        if current_key is not None:
                            print()  # keep the finished key's line on screen
                        current_key = kn
                        current_count = 0
                    current_count += 1
                    print_progress()

                held.add(kn)
            else:
                held.discard(kn)

    except KeyboardInterrupt:
        print()
        print('Stopped.')


main()
