# Audio Setup — PAM8406 Amp via the 3.5mm Jack

Hardware: Raspberry Pi 3 Model B (Rev 1.2), a PAM8406 class-D amp board, two
speakers, connected through the Pi's built-in 3.5mm AV jack. Display is
HDMI-only (no speakers), so the analog jack is the only audio output that
matters here.

## TL;DR — The Fix

The Pi has **two separate ALSA sound cards** and it's easy to test the wrong
one:

```
card 0: vc4hdmi     [vc4-hdmi]           — HDMI audio (no speakers on this display)
card 1: Headphones  [bcm2835 Headphones] — the analog 3.5mm jack you actually want
card 2: Pico        [USB-Audio]          — the keyboard project's own Pico, enumerates as a sound card
```

Find your own card numbers (they can differ by OS image/revision):

```
aplay -l
cat /proc/asound/cards
```

Test the *analog* card directly, bypassing PipeWire, to confirm the hardware
path works at all:

```
speaker-test -D plughw:1,0 -c2 -twav -l1
```

Make sure PipeWire's default output sink is the analog device, not HDMI:

```
wpctl status                 # look under Audio → Sinks for the "*" (default) marker
wpctl set-default <id>       # id of "Built-in Audio Stereo" (NOT the one labeled "(HDMI)")
wpctl set-mute <id> 0
wpctl set-volume <id> 100%
```

Confirm PipeWire itself can play sound through it:

```
pw-play /usr/share/sounds/alsa/Front_Center.wav
```

**Persist across reboot** — two layers need saving, PipeWire's default-sink
preference and the raw ALSA hardware mixer level:

```
wpctl set-default <id>              # WirePlumber remembers this by device name, survives reboot
amixer -c 1 sset PCM 100% unmute    # raw hardware gain — resets on reboot unless saved
sudo alsactl store 1                # writes card 1's mixer state to /var/lib/alsa/asound.state,
                                     # reloaded automatically at boot by the alsa-restore service
```

Verify with a reboot:

```
sudo reboot
# after it comes back:
wpctl status
speaker-test -D plughw:1,0 -c2 -twav -l1
```

`wpctl status` will show a new numeric sink id (ids are reassigned every
boot) but the same device should still be marked default `*`, and
`Settings → Default Configured Devices` should list something like
`alsa_output.platform-3f00b840.mailbox.stereo-fallback` — that's the
persisted preference, keyed by device name rather than the id.

### Two things that look like bugs but aren't

- **50Hz hum when you touch the bare jack, before anything is really
  playing.** Normal. A high-impedance analog audio line picks up ambient
  mains hum capacitively through your body when touched. It doesn't indicate
  a fault. If the hum persists *during actual playback*, that's a different
  problem — almost always a ground loop between the Pi's power supply and
  the amp's power supply if they're on separate wall adapters. Fix by
  sharing a common ground (power the PAM8406 from the Pi's own 5V rail, or
  put both PSUs on the same power strip) or adding an inline ground-loop
  isolator.
- **`amixer` reports `Playback channels: Mono` for card 1's `PCM` control.**
  That's describing the *mixer control*, not the audio stream. Capabilities
  `pvolume-joined pswitch-joined` mean the Pi's onboard PWM-based DAC only
  exposes one shared volume/mute register for both channels — there's no
  independent L/R gain in hardware. The actual PCM path is genuine 2-channel
  stereo, confirmed by `speaker-test -c2` announcing distinct "Front Left" /
  "Front Right" and both speakers working independently through the
  PAM8406.
- **Card 2, `Pico [USB-Audio]`, isn't a real audio device either.** It's
  the keyboard project's own Raspberry Pi Pico. CircuitPython enables a USB
  MIDI interface by default, and USB MIDI streaming is technically a
  subclass of the USB *Audio* class, so Linux's `snd-usb-audio` driver
  picks it up as a sound card even though no real audio is involved. It's
  not the cause of any audio bug here, but it's worth silencing so it can't
  confuse future diagnostics (or ever become a stray default sink via
  WirePlumber's hotplug auto-switching, see step 7). Create `boot.py`
  alongside `code.py` on the `CIRCUITPY` drive:

  ```python
  import usb_midi

  usb_midi.disable()
  ```

  `boot.py` only runs on a full boot, not on the auto-reload triggered by
  saving `code.py` — unplug and replug the Pico (or press its reset button)
  for this to take effect. See the main `README.md`'s "Disable USB MIDI"
  section.

---

## Diagnostic Journey — How We Got Here

### 1. The symptom

No sound at all through the PAM8406 + speakers when connected via the
3.5mm jack. Touching the bare jack produced a 50Hz hiss on both channels.
Working theory going in: the Pi is routing audio to HDMI, and the HDMI
display has no speakers to reveal that.

### 2. Identify the audio stack

```
pactl --version 2>/dev/null && echo "PulseAudio"
wpctl status 2>/dev/null && echo "PipeWire"
```

Result: PipeWire 1.4.2 (Raspberry Pi OS Bookworm default), not PulseAudio.
This determined which command family to use for the rest of the
investigation (`wpctl`/`pw-*` instead of `pactl`).

### 3. First look at `wpctl status`

```
wpctl status
```

Showed two sinks:

```
35. Built-in Audio Digital Stereo (HDMI) [vol: 0.40]
58. Built-in Audio Stereo               [vol: 1.00]   ← marked default (*)
```

This complicated the initial "it's routed to HDMI" theory — PipeWire
already believed the analog sink was default, at full volume, unmuted.
Something below the PipeWire layer had to be the culprit.

### 4. Rule out a muted/zero PipeWire sink and a jack-less Pi 5

```
wpctl get-volume 58        # → Volume: 1.00, not [MUTED]
cat /proc/device-tree/model # → Raspberry Pi 3 Model B Rev 1.2
```

The volume readout confirmed the sink wasn't secretly muted at the
PipeWire layer. The model check ruled out a real gotcha: the Raspberry Pi 5
removed the analog 3.5mm audio jack entirely, so a "healthy-looking" ALSA
node can exist in software with no physical jack behind it. Not the case
here — a Pi 3B genuinely has the jack.

### 5. Drop to the raw ALSA mixer

```
amixer -c 0 controls
```

```
numid=1,iface=CARD,name='HDMI Jack'
numid=6,iface=MIXER,name='PCM Playback Volume'
numid=5,iface=PCM,name='ELD'
numid=4,iface=PCM,name='IEC958 Playback Default'
numid=3,iface=PCM,name='IEC958 Playback Mask'
numid=2,iface=PCM,name='Playback Channel Map'
```

The controls on card 0 are all HDMI-specific (`HDMI Jack`, `ELD`,
`IEC958`/S/PDIF). **Card 0 is the HDMI audio card, not the analog jack.**
Any test run against `hw:0` or `plughw:0,0` was silently testing the wrong
device the entire time.

### 6. Confirm the wrong-card theory

```
speaker-test -D plughw:0,0 -c2 -twav -l1
```

Silent, as expected — this was playing to the HDMI card, and the monitor
has no speakers.

### 7. Enumerate the real cards

```
aplay -l
cat /proc/asound/cards
```

```
card 0: vc4hdmi        - vc4-hdmi
card 1: Headphones     - bcm2835 Headphones     ← the real analog jack
card 2: Pico           - USB-Audio, Raspberry Pi Pico
```

Card 1 is the actual analog output. Card 2 was an unexpected find: the
Toshiba keyboard's own Pico microcontroller enumerates as a USB audio
device on this machine, purely incidental to this repo's KMK firmware
project. Not the cause of the silence, but flagged as a future gotcha —
WirePlumber tends to auto-switch its default sink to the most recently
connected audio device, so unplugging/replugging the keyboard could
someday flip default output away from the speakers.

### 8. Test the correct card

```
speaker-test -D plughw:1,0 -c2 -twav -l1   # ALSA-direct, bypassing PipeWire — worked
pw-play /usr/share/sounds/alsa/Front_Center.wav  # through PipeWire's existing default sink — also worked
```

Both worked. Conclusion: there never was a real routing bug — PipeWire had
the correct analog sink set as default from the start. Every earlier
"no sound" result was from pointing test commands (`plughw:0,0`) at the
HDMI card by mistake.

### 9. Make it durable

Since the working state was arrived at manually mid-session, the last step
was ensuring it survives a reboot rather than reverting to whatever
PipeWire/ALSA pick by default:

```
wpctl set-default 58
wpctl set-mute 58 0
wpctl set-volume 58 100%
amixer -c 1 sset PCM 100% unmute
sudo alsactl store 1
sudo reboot
```

### 10. Verify persistence

Post-reboot:

```
wpctl status
```

```
45. Built-in Audio Digital Stereo (HDMI) [vol: 0.40]
55. Built-in Audio Stereo               [vol: 1.00]   ← still marked default (*)
...
Settings
 └─ Default Configured Devices:
         0. Audio/Sink alsa_output.platform-3f00b840.mailbox.stereo-fallback
```

The sink's numeric id changed (58 → 55, ids are reassigned every boot) but
it's still the default, at full volume, and the `Default Configured
Devices` entry shows WirePlumber persisted the choice by device name —
exactly what `wpctl set-default` is supposed to produce.

### 11. One last loose end: "why does it say Mono?"

```
amixer -c 1 sset PCM 100% unmute
```

```
Simple mixer control 'PCM',0
  Capabilities: pvolume pvolume-joined pswitch-joined
  Playback channels: Mono
  Limits: Playback -10239 - 400
  Mono: Playback 400 [100%] [4.00dB] [on]
```

`pvolume-joined pswitch-joined` means the volume and mute switch are a
single control shared by both channels — the Pi's onboard PWM-based analog
DAC just doesn't expose independent per-channel gain in hardware. That's
why the *simple mixer control* is labeled "Mono." The PCM audio stream
itself is real 2-channel stereo, as already proven in step 8 by
`speaker-test -c2` announcing distinct Front Left / Front Right channels
and both speakers working correctly off the PAM8406.

### 12. Silencing the phantom sound card

Card 2 (`Pico [USB-Audio]`, spotted in step 7) turned out to be the
keyboard's own microcontroller, not anything audio-related — CircuitPython
enables a USB MIDI interface by default, and MIDI streaming is a subclass
of the USB Audio class, so `snd-usb-audio` claims it. It never caused this
particular bug, but left alone it's a standing risk for WirePlumber to
someday auto-switch default output to it on hotplug. Fixed at the source,
in the keyboard firmware repo, with `boot.py`:

```python
import usb_midi

usb_midi.disable()
```

After unplugging/replugging the Pico, `cat /proc/asound/cards` no longer
lists it.

## Cast of Commands

| Command | What it told us |
|---|---|
| `pactl --version` / `wpctl status` | Which audio server is running (PipeWire, not Pulse) |
| `wpctl status` | Sink list, which one is default, software volume |
| `wpctl get-volume <id>` | Whether a sink is muted at the PipeWire layer |
| `cat /proc/device-tree/model` | Confirms the board actually has a physical 3.5mm jack (Pi 5 doesn't) |
| `amixer -c <N> controls` / `scontrols` | Raw ALSA mixer controls for a card — reveals what the card actually *is* (HDMI vs analog) |
| `aplay -l` / `cat /proc/asound/cards` | Ground-truth list of ALSA card indices and names |
| `speaker-test -D plughw:<N>,0 -c2 -twav -l1` | ALSA-direct playback test, bypassing PipeWire entirely |
| `pw-play <file>` | Playback test through PipeWire's current default sink |
| `wpctl set-default <id>` / `set-mute` / `set-volume` | Pin PipeWire's default sink, persisted by device name |
| `amixer -c <N> sset PCM 100% unmute` + `sudo alsactl store <N>` | Save the raw ALSA hardware mixer level so it survives reboot |
| `boot.py` with `usb_midi.disable()` (on the Pico) | Stops the keyboard's Pico from enumerating as a phantom `USB-Audio` sound card |
