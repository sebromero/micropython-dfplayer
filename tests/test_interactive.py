from machine import UART, Pin
from time import sleep_ms
from dfplayer import DFRobotPlayer, MH2024KPlayer

uart1 = UART(0, tx=Pin("TX"), rx=Pin("RX"))
uart2 = UART(1, tx=Pin("D9"), rx=Pin("D8"))
mhplayer = MH2024KPlayer(uart1)
mhplayer.volume = 50

dfrplayer = DFRobotPlayer(uart2, use_irq=True)
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

mhplayer.on_track_finished(lambda track: print(f"MH2024K Player finished track: {track}"))
dfrplayer.on_track_finished(lambda track: print(f"DFRobot Player finished track: {track}"))
