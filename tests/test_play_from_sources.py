from machine import UART, Pin
from time import sleep_ms
from dfplayer import DFRobotPlayer, GD3200Player, PlayerStatus

PLAY_WAIT_TIME_MS = 1000

uart1 = UART(0, tx=Pin("TX"), rx=Pin("RX"))
uart2 = UART(1, tx=Pin("D9"), rx=Pin("D8"))
gdplayer = GD3200Player(uart1)
dfrplayer = DFRobotPlayer(uart2)


def run_tests(player):
    print(f"Running status tests for {player.__class__.__name__}")
    player.stop()

    print("Playing MP3 track 1 from MP3 folder")
    player.play_from_mp3_folder(1)
    sleep_ms(PLAY_WAIT_TIME_MS) # Sometimes it takes a moment to start playing
    status = player.status
    if status != PlayerStatus.PLAYING:
        raise RuntimeError(f"Player did not enter PLAYING status after starting MP3 playback: {status}")
    else:
        print("✅ Status after starting MP3 playback correct")
    sleep_ms(2000)

    # WARN: On DFROBOTLISP3 the index might fall on a folder entry
    print("Playing track 2 by index from flattened file list")
    player.play_track_by_number(2)
    sleep_ms(PLAY_WAIT_TIME_MS) # Sometimes it takes a moment to start playing
    status = player.status
    if status != PlayerStatus.PLAYING:
        raise RuntimeError(f"Player did not enter PLAYING status after playing track by number: {status}")
    else:
        print("✅ Status after playing track by number correct")
    sleep_ms(2000)

    print("Playing track 2 from folder 1")
    player.play_track(1,2)
    sleep_ms(PLAY_WAIT_TIME_MS) # Sometimes it takes a moment to start playing
    status = player.status
    if status != PlayerStatus.PLAYING:
        raise RuntimeError(f"Player did not enter PLAYING status after playing track by folder and file number: {status}")
    else:
        print("✅ Status after playing track by folder and file number correct")
    sleep_ms(2000)

    player.stop()

run_tests(gdplayer)
run_tests(dfrplayer)