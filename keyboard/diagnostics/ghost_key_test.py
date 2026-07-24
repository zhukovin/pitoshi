"""
Ghost-key diagnostic for the Toshiba T1200XE matrix.

Talks straight to CircuitPython's keypad.KeyMatrix, bypassing KMK entirely, so
the raw electrical behavior of the matrix can be tested without any HID/OS
involvement. Nothing gets typed anywhere - results only go to the serial
console.

Usage:
  1. Back up the real CIRCUITPY/code.py, then copy this file over it.
  2. Open the serial console (see README: "Connecting to the Serial Console").
  3. Press Ctrl+D to (re)run it if it doesn't start automatically.
  4. Follow the prompts - press the named key repeatedly. Each key moves on
     automatically once a ghost is seen, or once PRESSES_PER_KEY clean presses
     are reached.
  5. Ctrl+C aborts and prints the summary so far.
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


def key_number(row, col):
    return row * NUM_COLS + col


def label(number):
    if 0 <= number < len(LABELS):
        return LABELS[number]
    return 'UNKNOWN(%d)' % number


NAME_TO_NUMBER = {name: n for n, name in enumerate(LABELS) if name != '--'}

# To re-test just one or two keys instead of walking the whole strip, list
# their names here, e.g. ONLY_TEST = ['F7']. Leave empty to test the whole
# F-key strip (cols 0-1, every row) in order.
ONLY_TEST = ['F7']

if ONLY_TEST:
    TEST_SEQUENCE = [NAME_TO_NUMBER[name] for name in ONLY_TEST]
else:
    TEST_SEQUENCE = [
        key_number(row, col)
        for row in range(8)
        for col in (0, 1)
    ]

PRESSES_PER_KEY = 100  # clean presses needed to pass a key with no ghost seen

matrix = keypad.KeyMatrix(
    row_pins=ROW_PINS,
    column_pins=COL_PINS,
    columns_to_anodes=False,  # matches DiodeOrientation.ROW2COL in code.py
    interval=0.002,
    debounce_threshold=15,
)


def test_key(expected):
    print()
    print('=== Press %s repeatedly (up to %d times) ===' % (label(expected), PRESSES_PER_KEY))
    print('    (moves on automatically once a ghost is seen, or the target is reached)')

    matrix.events.clear()
    press_count = 0
    expected_down = False
    episode_ghosts = set()

    while press_count < PRESSES_PER_KEY:
        ev = matrix.events.get()
        if ev is None:
            time.sleep(0.001)
            continue

        if ev.key_number == expected:
            if ev.pressed:
                expected_down = True
                episode_ghosts = set()
                press_count += 1
                if press_count % 10 == 0:
                    print('  %d/%d clean so far...' % (press_count, PRESSES_PER_KEY))
            else:
                expected_down = False
                if episode_ghosts:
                    names = ', '.join(label(g) for g in sorted(episode_ghosts))
                    print('  !! GHOST on press #%d: also saw [%s]' % (press_count, names))
                    return False
        else:
            if expected_down and ev.pressed:
                episode_ghosts.add(ev.key_number)

    print('  PASSED: %d clean presses, no ghosts.' % press_count)
    return True


def main():
    print()
    print('Ghost-key diagnostic - %d keys to test.' % len(TEST_SEQUENCE))
    results = []
    try:
        for kn in TEST_SEQUENCE:
            results.append((label(kn), test_key(kn)))
    except KeyboardInterrupt:
        print()
        print('Aborted.')

    print()
    print('=== Summary ===')
    for name, ok in results:
        print('  %-6s %s' % (name, 'OK' if ok else 'GHOSTED'))


main()
