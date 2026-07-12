import board

from kmk.kmk_keyboard import KMKKeyboard
from kmk.keys import KC
from kmk.modules.layers import Layers
from kmk.scanners import DiodeOrientation
from kmk.utils import Debug

# from kmk.scanners.keypad import MatrixScanner
from ghost_filter import GhostFilterMatrixScanner

Debug(__name__).enabled = True

# Copy this code to CIRCUITPY\code.py

keyboard = KMKKeyboard()
keyboard.modules.append(Layers())

keyboard.row_pins = (
    board.GP11, board.GP12, board.GP13, board.GP14,
    board.GP20, board.GP15, board.GP22, board.GP21,
)

keyboard.col_pins = (
    board.GP0, board.GP1, board.GP2, board.GP4,
    board.GP3, board.GP6, board.GP5, board.GP7,
    board.GP8, board.GP9, board.GP10,
)

# Toshiba matrix is active-high: rows HIGH, columns PULL_DOWN → ROW2COL.
keyboard.diode_orientation = DiodeOrientation.ROW2COL

# keypad.KeyMatrix default interval=0.02s (20ms/scan), threshold=1 = no debounce.
# debounce time = interval * threshold, so keep interval short and threshold moderate.
# interval=0.002 + threshold=15 → ~30ms debounce. Raise threshold if Enter still bounces.
keyboard.matrix = GhostFilterMatrixScanner(
# keyboard.matrix = MatrixScanner(
    column_pins=keyboard.col_pins,
    row_pins=keyboard.row_pins,
    columns_to_anodes=keyboard.diode_orientation,
    interval=0.002,
    debounce_threshold=15,
)

NO  = KC.NO
___ = KC.TRNS

keyboard.keymap = [
    # -----------------------------------------------------------------------
    # Layer 0 — base
    # -----------------------------------------------------------------------
    [
        # Col:  0        1        2        3        4        5        6        7        8        9        10
        KC.F1,  KC.F2,  KC.ESC,  KC.N2,  KC.N4,  KC.N6,  KC.N8,  KC.N0,   KC.EQL,  KC.BSPC, KC.PAUS,  # row 0
        KC.F11, KC.F12, KC.N1,   KC.N3,  KC.N5,  KC.N7,  KC.N9,  KC.MINS, KC.UP,   KC.DOWN, KC.MO(1), # row 1: Fn → MO(1)
        KC.F3,  KC.F4,  KC.TAB,  KC.W,   KC.R,   KC.Y,   KC.I,   KC.P,    KC.LBRC, KC.HOME, NO,       # row 2
        KC.PGDN,KC.PGUP,KC.Q,    KC.E,   KC.T,   KC.U,   KC.O,   KC.LEFT, KC.RBRC, KC.ENT,  NO,       # row 3
        KC.F5,  KC.F6,  KC.A,    KC.S,   KC.F,   KC.H,   KC.J,   KC.L,    KC.RIGHT,KC.GRV,  NO,       # row 4
        KC.F7,  KC.F8,  KC.LCTL, KC.D,   KC.G,   KC.B,   KC.K,   KC.SCLN, KC.QUOT, KC.RSFT, NO,       # row 5
        KC.F9,  KC.F10, KC.LSFT, KC.Z,   KC.V,   KC.N,   KC.COMM,KC.DOT,  KC.SLSH, KC.PSCR, NO,       # row 6
        KC.END, KC.LALT,KC.BSLS, KC.X,   KC.C,   KC.SPC, KC.M,   KC.DEL,  KC.CAPS, KC.INS,  NO,       # row 7
    ],
    # -----------------------------------------------------------------------
    # Layer 1 — Fn overlay
    #   Activated momentarily by holding Fn (MO(1)).
    #   Toggled permanently by Fn+F11 (TG(1)) = NumLock behaviour.
    #   Keys marked NO have Toshiba-specific functions (Slow/Fast CPU speed,
    #   IntDisp/ExtDisp display routing, Font size, Overlay mode) with no
    #   standard HID equivalent.
    #   Digits/operators use plain HID keyboard-page keys (KC.N4, KC.MINS, ...)
    #   rather than KC.KP_* (HID keypad-page). Keypad-page codes only resolve
    #   to digits when the host's own Num Lock is on, and this firmware can't
    #   read or drive that LED state — on Linux/RPi they were resolving as
    #   navigation keys (arrows/Home/etc.) instead of digits. Plain keys always
    #   type the digit/symbol regardless of host Num Lock state.
    # -----------------------------------------------------------------------
    [
    # Col:
    #   0         1               2        3    4    5      6      7        8        9    10
        ___,      ___,            NO,      ___, ___, ___,   KC.N8, KC.ASTR, ___,     ___, ___, # row 0: 8→8, 0→*; Esc→PopUp (no HID)
        KC.TG(2), KC.SCROLL_LOCK, ___,     ___, ___, KC.N7, KC.N9, ___,     ___,     ___, ___, # row 1: F11→TG(2) NumLock, F12→ScrLk, 7→7, 9→9
        ___,      ___,            ___,     ___, ___, ___,   KC.N5, KC.MINS, ___,     NO,  NO,  # row 2: i→5, p→-; Home→IntDisp (no HID)
        NO,       NO,             ___,     ___, ___, KC.N4, KC.N6, ___,     ___,     ___, NO,  # row 3: PgDn→Slow, PgUp→Fast (no HID); u→4, o→6
        ___,      ___,            ___,     ___, ___, ___,   KC.N1, KC.N3,   NO,      ___, NO,  # row 4: j→1, l→3; Right→Font (no HID)
        ___,      ___,            KC.LGUI, ___, ___, ___,   KC.N2, KC.PLUS, ___,     ___, NO,  # row 5: Ctrl→Cmd; k→2, ;→+
        ___,      NO,             ___,     ___, ___, ___,   ___,   KC.DOT,  KC.SLSH, ___, NO,  # row 6: F10→Overlay (no HID); .→., /→/
        NO,       ___,            ___,     ___, ___, ___,   KC.N0, ___,     ___,     ___, NO,  # row 7: End→ExtDisp (no HID); m→0
    ],
    # -----------------------------------------------------------------------
    # Layer 2 — NumLock (permanent numpad)
    #   Toggled on/off by Fn+F11 (TG(2) in layer 1).
    #   F11 alone also toggles it off (TG(2) here).
    #   Only numpad keys — no other Fn shortcuts — so normal keys like
    #   PgDn/PgUp/Home remain reachable when NumLock is on.
    #   Same plain-key rationale as layer 1 above.
    # -----------------------------------------------------------------------
    [
    # Col:
    #   0         1    2    3    4    5      6      7        8        9    10
        ___,      ___, ___, ___, ___, ___,   KC.N8, KC.ASTR, ___,     ___, ___, # row 0: 8→8, 0→*
        KC.TG(2), ___, ___, ___, ___, KC.N7, KC.N9, ___,     ___,     ___, ___, # row 1: F11→unlock NumLock, 7→7, 9→9
        ___,      ___, ___, ___, ___, ___,   KC.N5, KC.MINS, ___,     ___, NO,  # row 2: i→5, p→-
        ___,      ___, ___, ___, ___, KC.N4, KC.N6, ___,     ___,     ___, NO,  # row 3: u→4, o→6
        ___,      ___, ___, ___, ___, ___,   KC.N1, KC.N3,   ___,     ___, NO,  # row 4: j→1, l→3
        ___,      ___, ___, ___, ___, ___,   KC.N2, KC.PLUS, ___,     ___, NO,  # row 5: k→2, ;→+
        ___,      ___, ___, ___, ___, ___,   ___,   KC.DOT,  KC.SLSH, ___, NO,  # row 6: .→., /→/
        ___,      ___, ___, ___, ___, ___,   KC.N0, ___,     ___,     ___, NO,  # row 7: m→0
    ],
]

if __name__ == '__main__':
    keyboard.go()
