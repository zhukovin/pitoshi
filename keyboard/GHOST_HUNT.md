# The Ghost Hunt

### How a 1987 Toshiba keyboard, a Raspberry Pi Pico, and a service manual PDF conspired to teach me more about connector corrosion than I ever wanted to know.

---

## Prologue

This repo exists because a Toshiba T1200XE keyboard — the real deal, raw matrix, active-high rows, diode on every key — got a second life behind a Raspberry Pi Pico running [KMK](https://github.com/KMKfw/kmk_firmware). CircuitPython installed, matrix reverse-engineered, polarity quirks discovered the hard way (see the README's "Lessons Learned" — rows HIGH, columns pulled down, opposite of what every tutorial assumes). By the time the Fn layer and NumLock overlay were working, it felt done.

It was not done.

## Chapter 1 — Six Keys That Wouldn't Behave

The symptom showed up as double-vision on the function-key strip. Run `xev`, press a key, watch what comes out:

```
F3        -> F3, Next (PgDn)
F5        -> F5, F7
F7        -> F7, F9
F8        -> F8, F10
F9        -> F9, End
Next(PgDn)-> Next, F5
```

Six keys, all misbehaving, all producing exactly *one* extra keystroke each. And, separately, a seventh mystery: PrtSc produced nothing at all — not even a hint of activity.

The obvious question, and the one this whole hunt was really about: **is this hardware or software?** A 39-year-old keyboard and a freshly-written matrix scanner are both perfectly capable of being the culprit, and nothing about "I press one key, two happen" tells you which.

## Chapter 2 — Teaching the Firmware to Confess

The keymap looked clean — every matrix position mapped to exactly one key, no obvious dual-binding bug. But "the code looks right" isn't evidence. What was needed was a window into what the *matrix scanner itself* was seeing, before KMK's key-processing had a chance to touch it.

KMK already had the hook for this — one flag flip:

```python
Debug(__name__).enabled = True
```

...and a serial console (`screen /dev/tty.usbmodemXXXX 115200`) turned the Pico into a live logger of every raw scan event. Press F3, and instead of guessing, you'd *see* this:

```
395179 kmk.keyboard: <Event: key_number 22 pressed>: KeyboardKey(code=60)
395221 kmk.keyboard: <Event: key_number 33 pressed>: KeyboardKey(code=78)
395297 kmk.keyboard: <Event: key_number 22 released>: KeyboardKey(code=60)
395308 kmk.keyboard: <Event: key_number 33 released>: KeyboardKey(code=78)
```

Two genuinely distinct matrix positions (`22` and `33`) firing from one physical keypress. Case closed on "is this a firmware keymap bug" — it flatly wasn't. The ghost was happening at the electrical level, before software ever got a vote. **Hardware, confirmed.**

But *what kind* of hardware fault was still wide open.

## Chapter 3 — Finding the Shape of the Problem

With `key_number = row × 11 + col` in hand, the six broken pairs turned into coordinates, and the coordinates turned into a pattern: every ghost was the **same column, the next row in scan order** — a chain running row 2 through row 7. Rows 0 and 1 (F1/F2, F11/F12) sat outside it entirely.

That looked like a smoking gun for a scanning-timing artifact — until a control test broke the theory cleanly. TAB lives at row 2, column 2, right next to F3's row 2, column 0. If the *row* itself were compromised, TAB should ghost into Q below it exactly like F3 ghosts into PgDn.

TAB was rock solid. Every single time.

So the fault wasn't "row 2's wire is bad" — it was specific to *columns 0 and 1*, the narrow two-column strip where all the F-keys live. Theory revised: something localized to that F-key strip, not the row conductors generally.

Then a second axis showed up, unannounced. Pressing F12 occasionally produced F12 *and* F11 — a same-row, neighboring-*column* ghost, the mirror image of the row-axis chain:

```
!! GHOST: F12 press also saw F11, ~40ms later, intermittent (~29% of presses)
```

And then F4 → F3, which turned out to be the most reliable ghost of the entire investigation — **100% reproducible**, a tight and consistent ~15ms lag every single time, versus the 12-70ms jittery lag everywhere else. Not all ghosts were equal; some pairs had a much more "established" fault than others.

By now there were two independent axes of crosstalk (row-adjacent *and* column-adjacent), variable intermittency per pair, and a working hypothesis: **general degradation across the whole F-key strip**, not one single crack in one single spot.

## Chapter 4 — Ruling Out the Diode

A keyboard where "every key has a diode" invites an obvious question: is a bad diode doing this? The answer turned out to be no, and *why not* is worth remembering: a per-key diode sits in series with its own switch. A shorted F3 diode wouldn't make col0 spike only when F4 is pressed — it would make F3 fire on *every single scan* of its row, constantly, since diode current doesn't care whether F4 is pressed at all. That's not what was happening. The real requirement was a path that bypassed the switches and diodes entirely — a bridge directly between two column (or row) *traces*.

And the fact that the ghosting only ever ran one direction (F4→F3, never F3→F4) pointed at something specific: not a clean resistive short, but something with a built-in asymmetry — corrosion between two copper surfaces can behave like an accidental rectifying junction (the "rusty bolt effect"), conducting one way far better than the other. Nobody needed to open the keyboard to guess this; it was a prediction the evidence made *before* the connector was ever inspected.

## Chapter 5 — Building Instruments

Eyeballing debug logs one keypress at a time doesn't scale to "let's get a statistically convincing number of samples." So the toolbox grew:

- **`diagnostics/ghost_key_test.py`** — talks straight to `keypad.KeyMatrix`, bypassing KMK and the OS entirely. Walks a target key, counts clean presses, and the instant a ghost shows up mid-press it prints exactly what leaked in and moves on. First real-world run: pointed at F7, ghost caught on **press #1**.
- **`diagnostics/pattern_anomaly_test.py`** — the free-form version. No fixed target, no script to follow — just mash the keyboard naturally, and it watches for any key showing up while another is still held (which should never happen if you're only pressing one key at a time). Catches anomalies anywhere on the board, not just the already-known F-key suspects, and prints them as a compact pattern:

  ```
  !! I saw this pattern "aaabaaa" - is that intended?
     a=F7, b=F9
  ```

  with a live single-line counter (`F7 x7`) that keeps ticking through the noise, only breaking to a new line when you genuinely switch keys.

The full-strip walk of `ghost_key_test.py` actually produced a false-negative-*looking* result once — F7 tested clean after a 500-press slog through F1 through F6 first. Not a bug: it just never got a fair shot at F7 before patience ran out. Lesson learned and folded back into the tool: an `ONLY_TEST = ['F7']` override to jump straight to the key in question, which is exactly what caught the ghost on the very next attempt.

## Chapter 6 — The PCB, the Tape, and an Alibi

A scan of the keyboard PCB's solder side came next — dense fields of solder joints, scattered black axial diodes, and a Sumitomo FFC ribbon exiting toward what used to be the system board. Two blue tape flags marked, by hand, the physical locations the multimeter should care about: F7 and F9.

Zooming into those tape marks (a few rounds of `sips --cropOffset` standing in for a proper macro lens) revealed tiny silkscreened reference numbers: **118** and **120**. And sitting silently *between* them, unmarked: **119** — almost certainly F8.

That was a small, sharp piece of evidence. If the fault were simple physical adjacency — two neighboring pads on the board touching — F8 should be the first casualty, sitting as it does directly between F7 and F9. It wasn't (on that axis, anyway — more on that in a moment). Whatever was bridging row 5 and row 6 wasn't happening at the keyswitch pads at all. It was happening somewhere else entirely.

## Chapter 7 — The Rosetta Stone

The somewhere else turned out to be hiding in plain sight, in a page from Toshiba's own service manual: **Table B-14, Keyboard I/F connector pin assignment**. Eleven `KBOT` column-strobe lines, eight `KBRT` row-return lines, each with its own connector pin number.

Lining that table up against `code.py`'s oddly-jumbled `row_pins` tuple (`GP11, GP12, GP13, GP14, GP20, GP15, GP22, GP21` — which never made much sense as a deliberate GPIO choice) suddenly explained everything: it wasn't random at all. It was simply the connector's pins, 14 through 22, wired in physical order to whatever Pico pin was next in reach. Once that clicked, every single ghost pair could be translated into **connector pin numbers**:

| Ghost pair | Connector pins | Adjacent? |
|---|---|---|
| F3 → PgDn | 16 ↔ 17 | yes |
| F5 → F7 | 19 ↔ 20 | yes |
| **F7 → F9** | **20 ↔ 21** | **yes** |
| F9 → End | 21 ↔ 22 | yes |
| F4 → F3 | 2 ↔ 1 | yes |
| F12 → F11 | 2 ↔ 1 | yes (same pins) |
| PgDn → F5 | 17 ↔ 19 | one pin gap (GND) |

Six of seven ghosts, every single one, mapped onto **physically adjacent pins on the keyboard's own connector**. Not the PCB matrix. Not the keyswitches. The connector itself — most likely corrosion or contamination bridging neighboring contacts on a decades-old ribbon interface. It also closed the loop on F8's alibi from Chapter 6: F8 was never innocent, it just ghosts through *its own* row-mate pin (into F10, right there in the original six symptoms from Chapter 1) rather than through its physical neighbor on the PCB. Once you're looking at the connector instead of the board, F8's behavior stops being a mystery and becomes confirmation.

## Chapter 8 — Chasing a Ghost That Wouldn't Sit Still

Armed with exact pin numbers, a multimeter in diode-test mode should have been able to close this out. It didn't — every reading at rest came back `1.` (open), on every polarity, on every pin pair. That wasn't a dead end, though; it was consistent with everything already known. The ghost was never a hard, permanent short — it fired on roughly 40-100% of presses depending on the pair, with 10-70ms of jitter and inconsistent release ordering. A DMM sampling a couple of times a second was never going to catch something that transient.

That pushed the investigation toward an oscilloscope setup — trigger on the legitimate keypress, watch the *victim* column line (not the actively-driven row line, which a healthy push-pull output would just stomp flat regardless of a marginal leak) for an unexplained pulse riding in on the neighboring row's timeslot. Persistence mode, mash the key a few dozen times, let the rare ~40% events paint themselves onto the screen as a visibly distinct trace. The plan was solid. It never had to be executed.

## Chapter 9 — The Software Band-Aid

While the physical fix was still an open question, there was no reason to keep living with doubled keystrokes. Since every ghost pair was now precisely characterized — which key triggers which, and roughly how long the lag runs — the fix could be pushed into firmware as a stopgap: **`ghost_filter.py`**, a thin wrapper around `MatrixScanner` that watches raw `key_number` events, and if a known ghost key's press shows up within 200ms of its trigger while the trigger is still held, eats both the press and its matching release before KMK's core ever sees them.

```python
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
```

Deliberately a mitigation, not a cure — it masks the symptom at the cost of a small risk (fine here, since none of these pairs are ever used back-to-back on purpose) and does nothing if the underlying fault ever gets worse. But it meant the keyboard was fully usable while the actual hardware investigation kept going in the background.

## Chapter 10 — The Cure

In the end, the fix was almost anticlimactic compared to the investigation: **isopropyl alcohol**, applied to the connector contacts the service-manual table had pointed to, cleaned away whatever film — corrosion, oxidation, decades of dust — had been marginally bridging those neighboring pins. Ghosting: gone.

It's a satisfying ending precisely *because* it matches the theory built chapter by chapter: an intermittent, force-dependent, one-directional, connector-localized fault is exactly what a thin layer of contamination between two adjacent contacts looks like — and exactly what a swab of IPA fixes.

## Epilogue — The One That Got Away

PrtSc never got its resolution, and it's worth recording *why* it was set aside rather than pretending it was solved. The debug log settled the hardware question decisively:

```
721131 kmk.keyboard: <Event: key_number 75 pressed>: KeyboardKey(code=70)
```

Code 70 is the correct, standard HID usage for Print Screen. The switch, the matrix, and KMK all do their job perfectly. Whatever swallows PrtSc before it reaches `xev` lives downstream — almost certainly a desktop environment or screenshot utility holding a global grab on that key, a very ordinary X11 behavior that has nothing to do with a 1987 keyboard at all. Good to know, not worth chasing further.

## Cast of Tools

| Tool | Role |
|---|---|
| `xev` | Where the mystery started — first sighting of doubled keys |
| KMK `Debug` flag + serial console | Turned the firmware into an eyewitness |
| `diagnostics/ghost_key_test.py` | Scripted, repeatable per-key ghost testing |
| `diagnostics/pattern_anomaly_test.py` | Free-form, whole-keyboard anomaly watch |
| Multimeter (continuity + diode-test mode) | Ruled permanent shorts in and out |
| PCB photos + `sips` crops | Read the board's own silkscreen for ground truth |
| Toshiba service manual, Table B-14 | The Rosetta Stone — pin numbers that cracked the whole case |
| `ghost_filter.py` | The stopgap that kept the keyboard usable mid-investigation |
| Isopropyl alcohol | The actual cure |

## Lessons for Fellow Ghost Hunters

1. **Push the observation point as close to the hardware as you can.** `xev` told us *that* something was wrong; KMK's raw `key_number` log told us *where*, at the electrical level, before any software could be blamed or exonerated.
2. **Let control tests kill your theories.** TAB not ghosting is what actually saved this investigation from stalling on a wrong hypothesis about row conductors.
3. **A photo with a ruler (or in this case, a service manual with pin numbers) beats a guess every time.** The connector table did more in one afternoon than every prior physical inspection combined.
4. **Intermittent and directional is a different animal from "shorted."** Timing jitter and one-way conduction are themselves evidence — they pointed at corrosion long before any cleaning happened.
5. **A software mitigation is not admitting defeat.** Shipping `ghost_filter.py` bought a fully usable keyboard while the real fix was still being hunted down — and it's still sitting there, harmless, now that it has nothing left to catch.
