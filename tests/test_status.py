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

    status = player.status
    if status != PlayerStatus.STOPPED:
        raise RuntimeError(f"Read incorrect status after stop: {status}")
    else:
        print("✅ Status after stop correct")

    player.play()
    sleep_ms(250) # Sometimes it takes a moment to start playing
    status = player.status
    if status != PlayerStatus.PLAYING:
        raise RuntimeError(f"Read incorrect status after play: {status}")
    else:
        print("✅ Status after play correct")

    player.pause()
    status = player.status
    if status != PlayerStatus.PAUSED:
        raise RuntimeError(f"Read incorrect status after pause: {status}")
    else:
        print("✅ Status after pause correct")

    player.play()
    status = player.status
    if status != PlayerStatus.PLAYING:
        raise RuntimeError(f"Read incorrect status after resume: {status}")
    else:
        print("✅ Status after resume correct")

    player.stop()

run_tests(mhplayer)
run_tests(dfrplayer)