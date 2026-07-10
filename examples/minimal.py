from machine import UART, Pin
from dfplayer import DFPlayer

uart = UART(0, tx=Pin("TX"), rx=Pin("RX")) # Adjust pins as needed
player = DFPlayer(uart)
player.stop() # Stopping any current playback
player.volume = 50 # Setting volume to 50%
player.play() # Play first track