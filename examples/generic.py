from machine import UART, Pin
from time import sleep_ms
from dfplayer import DFPlayer, EqualizerMode, PlayerStatus

uart = UART(0, tx=Pin("TX"), rx=Pin("RX")) # Adjust pins as needed
# uart = UART(0, tx=Pin("D9"), rx=Pin("D8")) # Adjust pins as needed
busy_pin = Pin("D4") # Optional busy pin
player = DFPlayer(uart, busy_pin)

software_version = player.software_version
if software_version:
    print(f"Player software version: {software_version}")
else:
    print("Could not retrieve software version.")

print("Stopping any current playback")
player.stop()
print(f"Is stopped: {player.status == PlayerStatus.STOPPED}")

print("Setting volume to 40")
player.volume = 40

print("Play first track for 5 seconds")
player.play()

while player.status is None:
    print("Waiting for player to report status...")
    sleep_ms(50)

print(f"Is playing: {player.status == PlayerStatus.PLAYING}")
sleep_ms(5000)
print("Setting equalizer to POP and playing for 5 more seconds")
player.equalizer_mode = EqualizerMode.POP

sleep_ms(1000)
if player.equalizer_mode != EqualizerMode.POP:
    print(f"Warning: Equalizer mode should be POP but is {player.equalizer_mode}")
sleep_ms(5000)

print("Setting equalizer back to NORMAL")
player.equalizer_mode = EqualizerMode.NORMAL

for i in range(5):
    print("Decreasing volume")
    player.decrease_volume()
    print(f"Current volume: {player.volume}")
    sleep_ms(500)

sleep_ms(2000)

for i in range(5):
    print("Increasing volume")
    player.increase_volume()
    print(f"Current volume: {player.volume}")
    sleep_ms(500)

print("Pausing playback for 5 seconds")
player.pause()
print(f"Is paused: {player.status == PlayerStatus.PAUSED}")
sleep_ms(5000)

print("Resuming playback for 10 seconds")
player.play()
sleep_ms(10000)

print("Muting volume for 5 seconds")
player.set_muted(True)
sleep_ms(5000)
player.set_muted(False)
sleep_ms(5000)

print("Play next track for 10 seconds")
player.next_track()
sleep_ms(10000)

print("Play previous track for 10 seconds")
player.previous_track()
sleep_ms(10000)

print("Playing track 2 from folder 1")
player.play_track(1, 2)
sleep_ms(10000)

print("Playing advertisement 1 from advert folder")
player.play_from_advert_folder(1)
sleep_ms(10000)

print("Playing track 1 from MP3 folder")
player.play_from_mp3_folder(1)
sleep_ms(10000)

print("Playing track 2 by index from flattened file list")
player.play_track_by_number(2)