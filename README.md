# 🎵 MicroPython DFPlayer Mini Library

A MicroPython library for controlling the DFPlayer Mini MP3 module over UART. Supports multiple chip variants and provides a clean, event-driven API for audio playback on any MicroPython-capable board.

## ✨ Features

- 🎵 **Playback Control**: Play, pause, stop, and navigate tracks
- 📁 **Folder-Based Playback**: Play tracks from numbered folders or the special `MP3` folder
- 📢 **Advertisement Tracks**: Interrupt current playback with a short clip and resume automatically
- 🔀 **Random & Loop Modes**: Play all tracks randomly, loop a single track, or repeat an entire folder
- 🔊 **Volume & Equalizer**: Set volume (0–100%) and choose from Normal, Pop, Rock, Jazz, Classic, or Bass EQ modes
- 🔔 **Event Notifications**: Callbacks for track-finished, media inserted/ejected, and device-ready events
- ⚡ **IRQ Support**: Optionally use UART interrupts for non-blocking frame reception
- 🔌 **Busy Pin Support**: Detect playback state via the hardware BUSY pin
- 🧩 **Chip Variant Support**: Dedicated sub-classes for the DFRobot LISP3 and MH2024K variants, plus a `RandomFolderPlayer` utility

## 📖 Documentation

For detailed information on commands, chip-specific quirks, and protocol notes see the [doc/](doc/) folder.

## ✅ Supported Boards

Any board that can run MicroPython and exposes a hardware UART interface is supported. Adjust the `UART` and `Pin` arguments to match your board's pinout:

```python
uart = UART(0, tx=Pin("TX"), rx=Pin("RX"))  # Generic pin names
uart = UART(0, tx=Pin("D9"), rx=Pin("D8"))  # Named pins e.g. Arduino Nano ESP32
uart = UART(1, tx=Pin(17), rx=Pin(16))      # Numeric GPIO e.g. ESP32
```

## 🔌 Wiring

Connect the DFPlayer Mini to your microcontroller over UART:

| DFPlayer Pin | Board Pin |
| :--- | :--- |
| VCC | 3.3 V or 5 V |
| GND | GND |
| RX | UART TX pin |
| TX | UART RX pin |
| BUSY *(optional)* | Any GPIO |

> **Note:** The BUSY pin is driven low while a track is playing. Pass the configured `Pin` object as `busy_pin` to the `DFPlayer` constructor to enable hardware-based playback state detection without polling.

## ⚙️ Installation

The easiest way is to use [mpremote and mip](https://docs.micropython.org/en/latest/reference/packages.html#packages):

```bash
mpremote mip install github:sebromero/micropython-dfplayer
```

## 🧑‍💻 Usage

### Minimal example

```python
from machine import UART, Pin
from dfplayer import DFPlayer

uart = UART(0, tx=Pin("TX"), rx=Pin("RX"))
player = DFPlayer(uart)
player.stop()       # Stop any ongoing playback
player.volume = 50  # Set volume to 50 %
player.play()       # Play the first track
```

### Event notifications

Register callbacks to react to hardware events without polling:

```python
from machine import UART, Pin
from time import sleep_ms
from dfplayer import DFPlayer

uart = UART(0, tx=Pin("TX"), rx=Pin("RX"))
player = DFPlayer(uart)

player.on_device_ready(lambda data: print(f"Player ready: {hex(data)}"))
player.on_track_finished(lambda track: print(f"Finished track: {track}"))
player.on_media_inserted(lambda media: print(f"Media inserted: {hex(media)}"))
player.on_media_ejected(lambda media: print(f"Media ejected: {hex(media)}"))

player.volume = 50
player.play()

while True:
    player.update()  # Not needed when use_irq=True
    sleep_ms(100)
```

### Chip-specific variants

Use the dedicated sub-class that matches the chip on your module:

```python
from dfplayer import DFRobotPlayer  # DFRobot LISP3 (current genuine)
from dfplayer import MH2024KPlayer  # MH2024K clone
```

### Random folder playback

The `RandomFolderPlayer` utility plays all tracks in a folder in a random order:

```python
from machine import UART, Pin
from dfplayer import DFPlayer, RandomFolderPlayer

uart = UART(0, tx=Pin("TX"), rx=Pin("RX"))
busy_pin = Pin("D5")

player = DFPlayer(uart=uart, busy_pin=busy_pin, use_irq=True)
player.volume = 50

random_player = RandomFolderPlayer(player, delay_ms=2000, timer_id=1)
random_player.play_folder(1)  # Play all tracks in folder 01 randomly
```

### Developer setup

Clone the repository and run examples directly on the board using `mpremote`:

```bash
git clone https://github.com/sebromero/micropython-dfplayer
cd micropython-dfplayer
mpremote connect mount src run ./examples/minimal.py
```

## 🧩 Chip Compatibility

The DFPlayer Mini market is flooded with clones. Not all chips behave identically. The table below summarises the known variants and their compatibility with this library.

| Chip Label / Marking | Status | Compatibility | Known Issues & Quirks |
| :--- | :--- | :--- | :--- |
| **DFROBOT LISP3** | **Current Genuine** (Official) | **Excellent.** Works flawlessly with standard libraries out of the box. | **None.** This is the current proprietary chip used by DFRobot to defeat clones. It responds correctly to standard UART serial commands, processes volume controls accurately, and does not require artificial delays. |
| **YX5200-24SS** | **Legacy Genuine** / *High Fake Risk* | **Varies wildly** (Depends if it is real or counterfeit). | The original chip the libraries were built for. **However**, almost all modern chips with this label are counterfeits. Genuine ones work perfectly; fakes suffer from serial timeouts, incorrect file indexing, and sudden freezing. |
| **MH2024K-24SS**<br>**MH2024K-16SS** | **Clone** (Very Common) | **Poor.** Requires significant code modifications to work reliably. | **Severe timing issues.** You must add large delays (`delay(500)` to `delay(1000)`) after initializing and between serial commands. If you send commands too quickly, the chip ignores them or crashes. Often fails to read total folder/file counts correctly. |
| **GD3200B** | **Clone** (Common) | **Moderate.** Needs library tweaks or alternative libraries. | **Crashes on Query:** Frequently freezes if you use commands that ask the chip to return data (e.g., `readFileCounts()`, `readCurrentFileNumber()`). Playback commands work decently, but two-way communication is highly unstable. |
| **TD5580A** | **Clone** (Newer) | **Moderate.** Communicates with standard libraries, but hardware is severely compromised. | **Lost Audio Channels:** The speaker and line outputs are strictly Mono *without summation*. It only outputs the Left channel of the audio track. If you play a stereo file that pans sound to the right channel, that audio is completely lost.<br><br>**Poor Build Quality:** Boards with this chip (often marked HW-247A) have a high failure rate due to poorly soldered ground connections on the SD card reader. |
| **JC AA1752CJ**<br>*(and other JC labels)* | **Clone** | **Poor.** UART communication is heavily flawed. | **Acknowledge (ACK) Failures:** The chip often fails to send the required acknowledgment bytes back to the microcontroller, causing standard Arduino libraries to hang or report timeouts. Sometimes powers on at maximum volume and ignores initial volume commands. |
| **JL AA19H / AA20**<br>*(JieLi Series)* | **Clone** (Widespread) | **Moderate to Poor.** Missing features. | **Feature stripping.** These chips frequently lack hardware support for Equalizer (EQ) settings and native sleep modes. Some do not support the checksum validation standard to the DFPlayer protocol, meaning standard library commands might be misinterpreted. |
| **AS20H / AS21** | **Clone** | **Moderate.** Strict file requirements. | **Startup noise.** Often emits an audible "pop" or static hiss on startup. Extremely sensitive to SD card formatting. If the SD card is not fully formatted (not quick format) with strict `01/001.mp3` naming chronologically, it will refuse to play. |
| **Unlabeled / Blank** | **Clone** | **Unknown** | Utterly unpredictable. Some are rebranded MH2024K chips, while others are factory rejects. Behavior ranges from fully functional to completely dead on arrival. |

## 🐛 Reporting Issues

If you encounter any issue, please open a bug report [here](https://github.com/sebromero/micropython-dfplayer/issues).

## 💪 Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.


## 📜 License

This library is released under the [Mozilla Public License 2.0](LICENSE).
