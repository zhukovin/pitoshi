"""
Suppresses known ghost key-events caused by the hardware crosstalk on this
keyboard's connector (see README / diagnostics/ghost_key_test.py).

Wraps MatrixScanner and drops a ghost key's press+release if it appears
within GHOST_SUPPRESS_WINDOW seconds of its known trigger key while that
trigger is still held. Operates on raw key_number matrix events, below
KMK's key-processing, so it applies on every layer.

Trade-off: if a suppressed key is ever legitimately pressed within the
window while its trigger is held, that legitimate press is dropped too.
Only safe because none of these pairs are normally used in succession.
"""

import time

from kmk.scanners.keypad import MatrixScanner

GHOST_SUPPRESS_WINDOW = 0.2  # seconds; observed lag was 10-72ms

# trigger key_number -> set of ghost key_numbers to swallow if seen shortly
# after the trigger while it's still held. key_number = row * 11 + col.
GHOST_MAP = {
    22: {33},  # F3 -> PgDn/Next
    33: {44},  # PgDn/Next -> F5
    44: {55},  # F5 -> F7
    55: {66},  # F7 -> F9
    66: {77},  # F9 -> End
    56: {67},  # F8 -> F10
    12: {11},  # F12 -> F11
    23: {22},  # F4 -> F3
}


class GhostFilterMatrixScanner(MatrixScanner):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._held_triggers = {}  # key_number -> press timestamp
        self._suppressing = set()  # ghost key_numbers currently being eaten

    def scan_for_changes(self):
        while True:
            ev = super().scan_for_changes()
            if ev is None:
                return None

            kn = ev.key_number

            if kn in self._suppressing:
                if not ev.pressed:
                    self._suppressing.discard(kn)
                continue

            if ev.pressed:
                now = time.monotonic()
                ghosted = False
                for trig, ghosts in GHOST_MAP.items():
                    if (
                        kn in ghosts
                        and trig in self._held_triggers
                        and now - self._held_triggers[trig] <= GHOST_SUPPRESS_WINDOW
                    ):
                        ghosted = True
                        break
                if ghosted:
                    self._suppressing.add(kn)
                    continue
                if kn in GHOST_MAP:
                    self._held_triggers[kn] = now
            else:
                self._held_triggers.pop(kn, None)

            return ev
