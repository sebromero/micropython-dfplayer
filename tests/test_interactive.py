from machine import UART, Pin
from time import sleep_ms
from dfplayer import DFRobotPlayer, GD3200Player

uart1 = UART(0, tx=Pin("TX"), rx=Pin("RX"))
uart2 = UART(1, tx=Pin("D9"), rx=Pin("D8"))
gdplayer = GD3200Player(uart1)
gdplayer.volume = 50

dfrplayer = DFRobotPlayer(uart2)
dfrplayer.volume = 50

def get_frame_count(player):
    player._frame_reader.update()
    return player._frame_reader.available_frames()

def print_next_frame(player):
    player._frame_reader.update()
    frame = player._frame_reader.pop_frame()
    if frame:
        print(f"Frame: Command={hex(frame.command)} Data={hex(frame.data)}")
    else:
        print("No frame available")