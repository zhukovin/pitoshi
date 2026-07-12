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
    # -----------------------------------------------------------------------
    [
        # Col:  0           1                2   3    4    5          6          7                 8    9    10
        ___,    ___,         NO,             ___, ___, ___, KC.KP_8,  KC.KP_ASTERISK, ___,         ___, ___, # row 0: 8→KP8, 0→KP*; Esc→PopUp (no HID)
        KC.TG(2),KC.SCROLL_LOCK,___,        ___, ___, KC.KP_7, KC.KP_9, ___,         ___,         ___, ___, # row 1: F11→TG(2) NumLock, F12→ScrLk, 7→KP7, 9→KP9
        ___,    ___,         ___,            ___, ___, ___, KC.KP_5,  KC.KP_MINUS,    ___,         NO,  NO,  # row 2: i→KP5, p→KP-; Home→IntDisp (no HID)
        NO,     NO,          ___,            ___, ___, KC.KP_4, KC.KP_6, ___,         ___,         ___, NO,  # row 3: PgDn→Slow, PgUp→Fast (no HID); u→KP4, o→KP6
        ___,    ___,         ___,            ___, ___, ___, KC.KP_1,  KC.KP_3,        NO,          ___, NO,  # row 4: j→KP1, l→KP3; Right→Font (no HID)
        ___,    ___,         KC.LGUI,        ___, ___, ___, KC.KP_2,  KC.KP_PLUS,     ___,         ___, NO,  # row 5: Ctrl→Cmd; k→KP2, ;→KP+
        ___,    NO,          ___,            ___, ___, ___, ___,      KC.KP_DOT,      KC.KP_SLASH, ___, NO,  # row 6: F10→Overlay (no HID); .→KP., /→KP/
        NO,     ___,         ___,            ___, ___, ___, KC.KP_0,  ___,            ___,         ___, NO,  # row 7: End→ExtDisp (no HID); m→KP0
    ],
    # -----------------------------------------------------------------------
    # Layer 2 — NumLock (permanent numpad)
    #   Toggled on/off by Fn+F11 (TG(2) in layer 1).
    #   F11 alone also toggles it off (TG(2) here).
    #   Only numpad keys — no other Fn shortcuts — so normal keys like
    #   PgDn/PgUp/Home remain reachable when NumLock is on.
    # -----------------------------------------------------------------------
    [
        # Col:  0           1    2    3    4    5          6          7                 8              9    10
        ___,    ___,         ___, ___, ___, ___, KC.KP_8,  KC.KP_ASTERISK, ___,         ___,           ___, # row 0: 8→KP8, 0→KP*
        KC.TG(2), ___,       ___, ___, ___, KC.KP_7, KC.KP_9, ___,         ___,         ___,           ___, # row 1: F11→unlock NumLock, 7→KP7, 9→KP9
        ___,    ___,         ___, ___, ___, ___, KC.KP_5,  KC.KP_MINUS,    ___,         ___,           NO,  # row 2: i→KP5, p→KP-
        ___,    ___,         ___, ___, ___, KC.KP_4, KC.KP_6, ___,         ___,         ___,           NO,  # row 3: u→KP4, o→KP6
        ___,    ___,         ___, ___, ___, ___, KC.KP_1,  KC.KP_3,        ___,         ___,           NO,  # row 4: j→KP1, l→KP3
        ___,    ___,         ___, ___, ___, ___, KC.KP_2,  KC.KP_PLUS,     ___,         ___,           NO,  # row 5: k→KP2, ;→KP+
        ___,    ___,         ___, ___, ___, ___, ___,      KC.KP_DOT,      KC.KP_SLASH, ___,           NO,  # row 6: .→KP., /→KP/
        ___,    ___,         ___, ___, ___, ___, KC.KP_0,  ___,            ___,         ___,           NO,  # row 7: m→KP0
    ],
]

if __name__ == '__main__':
    keyboard.go()
