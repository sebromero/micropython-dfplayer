# Playing track 1 from MP3 folder
# Skipping notification code: 0x3d data: 0xe
# DEBUG: Discarding frame during clear. Code: 0x41 Data: 0x0
# Playing track 2 by index from flattened file list


from machine import UART, Pin
from time import sleep_ms
from dfplayer import DFRobotPlayer, GD3200Player, PlayerStatus

uart1 = UART(0, tx=Pin("TX"), rx=Pin("RX"))
uart2 = UART(1, tx=Pin("D9"), rx=Pin("D8"))
gdplayer = GD3200Player(uart1)
dfrplayer = DFRobotPlayer(uart2)

def run_tests(player):
    print(f"Running status tests for {player.__class__.__name__}")
    player.stop()

    print("Playing advertisement 1 from advert folder")
    player.play_from_advert_folder(1)
    status = player.status
    
    # No status available during advert playback
    if status != None:
        raise RuntimeError(f"Player did not enter PLAYING status after starting advert playback: {status}")
    else:
        print("✅ Status after starting advert playback correct")
    sleep_ms(2000)

    print("Playing MP3 track 1 from MP3 folder")
    player.play_from_mp3_folder(1)
    sleep_ms(250) # Sometimes it takes a moment to start playing
    status = player.status
    if status != PlayerStatus.PLAYING:
        raise RuntimeError(f"Player did not enter PLAYING status after starting MP3 playback: {status}")
    else:
        print("✅ Status after starting MP3 playback correct")
    sleep_ms(2000)

    print("Playing track 2 by index from flattened file list")
    player.play_track_by_number(2)
    sleep_ms(250) # Sometimes it takes a moment to start playing
    status = player.status
    if status != PlayerStatus.PLAYING:
        raise RuntimeError(f"Player did not enter PLAYING status after playing track by number: {status}")
    else:
        print("✅ Status after playing track by number correct")
    sleep_ms(2000)

    print("Playing track 2 from folder 1")
    player.play_track(1,2)
    sleep_ms(250) # Sometimes it takes a moment to start playing
    status = player.status
    if status != PlayerStatus.PLAYING:
        raise RuntimeError(f"Player did not enter PLAYING status after playing track by folder and file number: {status}")
    else:
        print("✅ Status after playing track by folder and file number correct")
    sleep_ms(2000)

    player.stop()

# run_tests(gdplayer)
run_tests(dfrplayer)