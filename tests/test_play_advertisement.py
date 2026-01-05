"""
To run this test, make sure you have the following files on the SD card:

- ADVERT/0001.mp3
"""

from machine import UART, Pin
from time import sleep_ms
from dfplayer import MH2024KPlayer, PlayerStatus

PLAY_WAIT_TIME_MS = 1000

uart1 = UART(0, tx=Pin("TX"), rx=Pin("RX"))
mhplayer = MH2024K(uart1)


def run_tests(player):
    print(f"Running status tests for {player.__class__.__name__}")
    player.stop()
    player.play()
    sleep_ms(PLAY_WAIT_TIME_MS) # Sometimes it takes a moment to start playing

    status = player.status
    if status != PlayerStatus.PLAYING:
        raise RuntimeError(f"Player did not enter PLAYING status after play(): {status}")
    else:
        print("✅ Status after play() correct")
    sleep_ms(2000)

    print("Playing advertisement 1 from advert folder")
    player.play_from_advert_folder(1)
    status = player.status

    # No status available during advert playback
    if status != None:
        raise RuntimeError(f"Player did not enter PLAYING status after starting advert playback: {status}")
    else:
        print("✅ Status after starting advert playback correct")
    sleep_ms(2000)

    player.stop()

run_tests(mhplayer)