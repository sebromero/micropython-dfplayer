from machine import UART, Pin
from time import sleep_ms
from dfplayer import DFPlayer

uart = UART(0, tx=Pin("TX"), rx=Pin("RX")) # Adjust pins as needed
player = DFPlayer(uart)

player.on_device_ready(lambda data: print(f"Player ready with data: {hex(data)}"))
player.on_track_finished(lambda track: print(f"Player finished track: {track}"))
player.on_media_inserted(lambda media: print(f"Player media inserted: {hex(media)}"))
player.on_media_ejected(lambda media: print(f"Player media ejected: {hex(media)}"))

player.stop() # Stopping any current playback
player.volume = 50 # Setting volume to 50%
player.play() # Play first track

print("Waiting for notifications...")
while True:
    player.update() # Not necessary if using IRQ mode
    sleep_ms(100)