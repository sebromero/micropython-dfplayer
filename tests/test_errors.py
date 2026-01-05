"""
To run this test, make sure you have the following files on the SD card:
- 01/001.mp3

Make sure you don't have:
- 09/255.mp3
"""
from machine import UART, Pin
from time import sleep_ms
from dfplayer import DFRobotPlayer, MH2024KPlayer, PlayerStatus

uart1 = UART(0, tx=Pin("TX"), rx=Pin("RX"))
uart2 = UART(1, tx=Pin("D9"), rx=Pin("D8"))
mhplayer = MH2024KPlayer(uart1)
dfrplayer = DFRobotPlayer(uart2)

def run_tests(player):
    print(f"Running status tests for {player.__class__.__name__}")
    player.stop()
    try:
        player.play_track(1,1)
    except Exception as e:
        raise RuntimeError("Failed to play track 1/1") from e
    print("✅ Playing track 1/1")

    sleep_ms(1000)
    player.stop()

    try:
        player.play_track(9,255)
    except Exception as e:
        print("✅ Correctly failed to play non-existing track 9/255")
    else:
        raise RuntimeError("Playing non-existing track 9/255 should have raised an exception")
    
    player.stop()

run_tests(mhplayer)
run_tests(dfrplayer)