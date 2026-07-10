from machine import UART, Pin
from time import sleep_ms
from dfplayer import DFRobotPlayer, MH2024KPlayer

from dfplayer.dfplayer import DFPLAYER_CMD_GET_VOLUME, DFPLAYER_CMD_GET_STATUS
from dfplayer.dfplayer import DFPLAYER_CMD_GET_VERSION, DFPLAYER_CMD_GET_EQUALIZER
from dfplayer.dfplayer import DFPLAYER_CMD_GET_PLAYBACK_MODE

uart1 = UART(0, tx=Pin("TX"), rx=Pin("RX"))
uart2 = UART(1, tx=Pin("D9"), rx=Pin("D8"))
mhplayer = MH2024KPlayer(uart1)
dfrplayer = DFRobotPlayer(uart2)

def get_response_time(player, command, timeout_ms=5000) -> int | None:  
    """
    Send a command to the player and measure the response time in milliseconds.
    Returns the response time in milliseconds, or None if no response is received within the timeout.    
    """
    import time
    start_time = time.ticks_ms()
    player._send_command(command)

    while True:
        if time.ticks_diff(time.ticks_ms(), start_time) > timeout_ms:
            return None
        
        player._frame_reader.update(timeout_ms=timeout_ms)
        available_frames = player._frame_reader.available_frames()
        
        if available_frames == 0:
            sleep_ms(1)
            continue
        
        for _ in range(available_frames):
            next_frame = player._frame_reader.pop_frame()
            if next_frame.command != command:
                continue
            
            end_time = time.ticks_ms()
            return time.ticks_diff(end_time, start_time)
        
players = [mhplayer, dfrplayer]
for player in players:
    print(f"Running test for {player.__class__.__name__}")
    response_time_volume = get_response_time(player, DFPLAYER_CMD_GET_VOLUME)
    print(f"Response time for volume: {response_time_volume} ms")
    response_time_status = get_response_time(player, DFPLAYER_CMD_GET_STATUS)
    print(f"Response time for status: {response_time_status} ms")
    response_time_version = get_response_time(player, DFPLAYER_CMD_GET_VERSION)
    print(f"Response time for version: {response_time_version} ms")
    response_time_eq = get_response_time(player, DFPLAYER_CMD_GET_EQUALIZER)
    print(f"Response time for equalizer: {response_time_eq} ms")
    response_time_mode = get_response_time(player, DFPLAYER_CMD_GET_PLAYBACK_MODE)
    print(f"Response time for playback mode: {response_time_mode} ms")
    print("-----")