# Author: Sebastian Romero

from micropython import const
from machine import Pin
from time import sleep_ms
import struct
from collections import deque

# CONFIG
DFPLAYER_DEFAULT_DELAY_MS = const(150) # Default delay after sending a command.
DFPLAYER_BOOTUP_TIME_MS = const(3000)  # Boot up of the device takes 1.5 to 3 secs.
DFPLAYER_TIMEOUT_MS = const(100)  # Default timeout waiting for a reply in milliseconds.

DFPLAYER_MAX_VOLUME = const(30)  # Maximum supported volume.
DFPLAYER_MAX_FOLDER = const(99)  # Highest supported folder number.
DFPLAYER_MAX_MP3_FILE = const(255)  # Highest supported file number in the "MP3" folder.
DFPLAYER_MAX_ADVERT_FILE = const(65536)  # Highest supported file number in the "ADVERT" folder.

# Constants used in frames sent to the DFPlayer Mini
DFPLAYER_FRAME_SIZE = const(10)  # Size of a frame sent to the DFPlayer Mini.
DFPLAYER_START = const(0x7e)  # Start symbol.
DFPLAYER_VERSION = const(0xff)  # Value to use in version field.
DFPLAYER_LEN = const(0x06)  # Length of a frame. (Command length)
DFPLAYER_NO_ACK = const(0x00)  # No acknowledgement of CMD required.
DFPLAYER_ACK = const(0x01)  # Acknowledgement of CMD required.
DFPLAYER_END = const(0xef)  # End symbol.

# UART settings of the DFPlayer Mini
DFPLAYER_BAUD = const(9600)  # Symbol rate of the DFPlayer mini.
DFPLAYER_DATA_BITS = const(8)  # The DFPlayer uses 8 data bits.
DFPLAYER_PARITY = const(None)  # The DFPlayer does not use a parity bit.
DFPLAYER_STOP_BITS = const(1)  # The DFPlayer uses 1 stop bit.

# Classes of messages received from the DFPlayer
#DFPLAYER_CLASS_MASK = const(0xf0)  # Use this mask to get the class from a response code.
#DFPLAYER_CLASS_NOTIFY = const(0x30)  # Message is an event notification (unrelated to any command)

# Bitmasks identifying the playback sources in the ready notification
#DFPLAYER_MASK_USB = const(0x01)  # USB stick is connected.
#DFPLAYER_MASK_SDCARD = const(0x02)  # SD-Card is connected.
#DFPLAYER_MASK_PC = const(0x04)  # Unclear, has something to do with debugging.
#DFPLAYER_MASK_FLASH = const(0x08)  # NOR flash is connected.

# Status bitmasks
DFPLAYER_STATUS_STOPPED = const(0x00) # The DFPlayer is currently stopped e.g. done playing a song.
DFPLAYER_STATUS_PLAYING = const(0x01) # The DFPlayer is currently playing a song.
DFPLAYER_STATUS_PAUSED  = const(0x02) # The DFPlayer is paused.

# Response codes sent by the DFPlayer
DFPLAYER_RESPONSE_ERROR = const(0x40)  # While processing the most recent command an error occurred.
DFPLAYER_RESPONSE_OK = const(0x41)  # Last command succeeded.

# Error codes sent as parameter of error messages
DFPLAYER_ERROR_NO_SUCH_FILE = const(0x06)  # File/folder selected for playback (command 0x06) does not exist.

# Common Commands
DFPLAYER_CMD_NEXT = const(0x01)  # Start playing the next song.
DFPLAYER_CMD_PREV = const(0x02)  # Start playing the next song.
DFPLAYER_CMD_PLAY_TRACK = const(0x03)  # Play the given track. (DFROBOT: 0-2999) (MH2024/GD3200: 0-65535)
DFPLAYER_CMD_VOLUME_INC = const(0x04)  # Increase volume.
DFPLAYER_CMD_VOLUME_DEC = const(0x05)  # Decrease volume.
DFPLAYER_CMD_SET_VOLUME = const(0x06)  # Set the volume to the given level. (0-30)
DFPLAYER_CMD_SET_EQUALIZER = const(0x07)  # Set the equalizer to the given setting. (0-5)
DFPLAYER_CMD_SET_SOURCE = const(0x09)  # Set the source to play files from.
DFPLAYER_CMD_STANDBY_ENTER = const(0x0a)  # Enter low power mode.
DFPLAYER_CMD_RESET = const(0x0c)  # Reset the DFPlayer Mini.
DFPLAYER_CMD_PLAY = const(0x0d)  # Start playing the selected file.
DFPLAYER_CMD_PAUSE = const(0x0e)  # Pause the playback.
DFPLAYER_CMD_STOP = const(0x16)  # Stop playback.
DFPLAYER_CMD_MUTE = const(0x1a)  # Mute/unmute the audio output. 0=unmute, 1=mute
DFPLAYER_CMD_FILE = const(0x0f)  # Play the given file (1-255) in the given folder (1-99)
DFPLAYER_CMD_PLAY_ADVERT = const(0x13)  # Play the given file (1-9999) from the folder "ADVERT", resume current playback afterwards.
# DFPLAYER_CMD_REPEAT_PLAYBACK = const(0x11)  # Start/stop repeat-playing the whole source. 1=loop 0=stop
DFPLAYER_CMD_GET_STATUS = const(0x42)  # Retrieve the current status.
DFPLAYER_CMD_GET_VOLUME = const(0x43)  # Retrieve the current volume.
DFPLAYER_CMD_GET_EQUALIZER = const(0x44)  # Retrieve the current equalizer setting.
# DFPLAYER_CMD_GET_MODE = const(0x45)  # Retrieve the current playback mode.
# DFPLAYER_CMD_GET_VERSION = const(0x46)  # Retrieve the device's software version.
# DFPLAYER_CMD_FILES_FLASH = const(0x49)  # Get the total number of files on the internal flash.
# DFPLAYER_CMD_FILENO_FLASH = const(0x4d)  # Get the currently select file number on the NOR flash.
DFPLAYER_CMD_INIT = const(0x3f)  # TODO e.g. get online devices

class Frame():
    def __init__(self, raw_data):
        if raw_data is None or len(raw_data) != DFPLAYER_FRAME_SIZE:
            raise ValueError(f"Frame data must be exactly {DFPLAYER_FRAME_SIZE} bytes")
        
        if raw_data[0] == DFPLAYER_START and raw_data[1] == DFPLAYER_VERSION and raw_data[2] == DFPLAYER_LEN and raw_data[9] == DFPLAYER_END:
            self.command = raw_data[3]
            self.data = struct.unpack('>H', raw_data[5:7])[0]
            self.raw_data = raw_data
        else:
            raise ValueError("Invalid frame received:", self._frame_as_string(raw_data))

    def __str__(self):
        return " ".join([hex(b) for b in self.raw_data])
    
class FrameReader():
    def __init__(self, uart):
        self.uart = uart
        self._frames = deque([], 10)  # Store up to 10 frames
        # TODO: Consider using IRQ on uart RX
        # On ESP32 it uses Timer(0) which makes it unavailable for other uses
        #uart.irq(handler= lambda e: print("UART IRQ fired!"), trigger=UART.IRQ_RXIDLE)

    def _clear_rx_buffer(self):
        avail_bytes = self.uart.any()
        self.uart.read(avail_bytes)

    def update(self):
        # TODO: Filter out System Responses
        while True:
            f = self._read_frame()
            if f is None:
                return
            self._frames.append(f)

    def available_frames(self):
        return len(self._frames)
    
    def pop_frame(self) -> Frame | None:
        if len(self._frames) == 0:
            return None
        return self._frames.popleft()
    
    def peek_frame(self) -> Frame | None:
        if len(self._frames) == 0:
            return None
        return self._frames[0]

    def _read_frame(self):
        if not self.uart.any():
            return None
    
        if self.uart.any() % DFPLAYER_FRAME_SIZE != 0:
            print("Warning: Incomplete frame in UART buffer, clearing buffer")
            self._clear_rx_buffer()
            return None
        
        return Frame(self.uart.read(DFPLAYER_FRAME_SIZE))

class PlayerStatus:
    STOPPED = 0
    PLAYING = 1
    PAUSED = 2

class EqualizerMode:
    NORMAL = 0
    POP = 1
    ROCK = 2
    JAZZ = 3
    CLASSIC = 4
    BASS = 5

class DFPlayer:    
    def __init__(self, uart, busy_pin = None):
        self.uart = uart
        uart.init(baudrate=DFPLAYER_BAUD, bits=DFPLAYER_DATA_BITS, parity=DFPLAYER_PARITY, stop=DFPLAYER_STOP_BITS, timeout=DFPLAYER_TIMEOUT_MS)
        self.busy_pin = busy_pin
        if busy_pin:
            self.busy_pin.init(Pin.IN)
            busy_pin.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self._on_busy_pin_change)
        
        self._frame_reader = FrameReader(uart)

    def _on_busy_pin_change(self, pin):
         # High level during playback; Low in pause status and module sleep
        self._playing = pin.value() == 0

    @property
    def playing(self):
        """Return True if the DFPlayer is currently playing a song."""
        if self.busy_pin: # If we have a busy pin, use it
            return self._playing
        return self.status == PlayerStatus.PLAYING

    def _send_command(self, command, data_high = 0x0, data_low = 0x0, ack = True):
        # Ensure command is only one byte long
        if command > 0xFF:
            raise ValueError("Command must be a single byte")
        if data_high > 0xFF or data_low > 0xFF:
            raise ValueError("Data high and low must be single byte values")
        frame_check_init = -(DFPLAYER_VERSION + DFPLAYER_LEN)
        ack_flag = DFPLAYER_ACK if ack else DFPLAYER_NO_ACK
        checksum = frame_check_init - (command + ack_flag + data_low + data_high)
        high_byte, low_byte = checksum >> 8, checksum & 0xFF
        frame = [DFPLAYER_START, DFPLAYER_VERSION, DFPLAYER_LEN, command, ack_flag, data_high, data_low, high_byte, low_byte, DFPLAYER_END]        
        frame = bytes([b & 0xFF for b in frame]) # Convert to unsigned bytes
        self.uart.write(bytes(frame))
        self.uart.flush() # Wait until all data is sent        

    def _handle_error_response(self, response_data):
        if response_data == DFPLAYER_ERROR_NO_SUCH_FILE:
            raise RuntimeError("No such file or folder")
        raise RuntimeError(f"Unknown error. Data: {hex(response_data)}")          

    def _exec_command(self, command, data_high = 0x0, data_low = 0x0, delay_ms = DFPLAYER_DEFAULT_DELAY_MS, ack = True, is_query = False, check_error = False):
        self._send_command(command, data_high, data_low, ack)
        sleep_ms(delay_ms)

        cmd_response = None
        
        # For queries it seems that first the query response is sent,
        # then the ACK/ERROR response.
        if is_query:
            self._frame_reader.update()
            cmd_response = self._frame_reader.pop_frame()
            if cmd_response.command != command:
                raise RuntimeError(f"Invalid response code received: {hex(cmd_response.command)} expected: {hex(command)}")

        if ack:
            self._frame_reader.update()
            ack_response = self._frame_reader.pop_frame()
            if ack_response.command != DFPLAYER_RESPONSE_OK:
                raise RuntimeError(f"Command {hex(command)} was not acknowledged. Received: {hex(ack_response.command)} data: {hex(ack_response.data)}")

        if not check_error:
            return cmd_response

        sleep_ms(25)  # Give some time before reading the error response
        self._frame_reader.update()
        error_response = self._frame_reader.pop_frame()
        
        # TODO: DEBUG, remove later
        if error_response is not None:
            print(f"Error response: {hex(error_response.command)} data: {hex(error_response.data)}")
        else:
            print("No error response received")

        if error_response and error_response.command == DFPLAYER_RESPONSE_ERROR:
            self._handle_error_response(error_response.data)

        return cmd_response

    def reset(self):
        """Reset the DFPlayer."""
        self._exec_command(DFPLAYER_CMD_RESET, ack=False, delay_ms=DFPLAYER_BOOTUP_TIME_MS)
        spurious_data = self.uart.any() % DFPLAYER_FRAME_SIZE
        if spurious_data > 0:
            # print(f"Clearing {spurious_data} bytes of spurious data from UART buffer after reset")
            self.uart.read(spurious_data)
        self._frame_reader.update()
        last_frame = self._frame_reader.peek_frame()
        if last_frame and last_frame.command == DFPLAYER_CMD_INIT:
            # print("Removing bootup OK response from frame reader")
            self._frame_reader.pop_frame()  # Remove the bootup OK response

    def next_track(self):
        self._exec_command(DFPLAYER_CMD_NEXT)
    
    def previous_track(self):
        self._exec_command(DFPLAYER_CMD_PREV)

    def play(self):
        self._exec_command(DFPLAYER_CMD_PLAY)

    def pause(self):
        self._exec_command(DFPLAYER_CMD_PAUSE)

    def stop(self):
        self._exec_command(DFPLAYER_CMD_STOP)

    def set_muted(self, muted : bool):
        """Mute or unmute the DFPlayer."""
        value = 0x01 if muted else 0x00
        self._exec_command(DFPLAYER_CMD_MUTE, 0x00, value)

    @property
    def equalizer_mode(self):
        """Return the current equalizer setting."""
        response_data = self._exec_command(DFPLAYER_CMD_GET_EQUALIZER, is_query=True).data
        if response_data == 0:
            return EqualizerMode.NORMAL
        if response_data == 1:
            return EqualizerMode.POP
        if response_data == 2:
            return EqualizerMode.ROCK
        if response_data == 3:
            return EqualizerMode.JAZZ
        if response_data == 4:
            return EqualizerMode.CLASSIC
        if response_data == 5:
            return EqualizerMode.BASS
        return None
    
    @equalizer_mode.setter
    def equalizer_mode(self, value: EqualizerMode):
        """Set the equalizer mode."""
        if value < 0 or value > 5:
            raise ValueError("Equalizer mode must be between 0 and 5")
        self._exec_command(DFPLAYER_CMD_SET_EQUALIZER, 0x00, value)

    def increase_volume(self):
        self._exec_command(DFPLAYER_CMD_VOLUME_INC)

    def decrease_volume(self):
        self._exec_command(DFPLAYER_CMD_VOLUME_DEC)
    
    @property
    def volume(self):
        response_data = self._exec_command(DFPLAYER_CMD_GET_VOLUME, is_query=True).data
        return int(response_data / DFPLAYER_MAX_VOLUME * 100)

    @volume.setter
    def volume(self, value : int):
        """Set the volume of the DFPlayer in percent (0-100%)."""
        if value < 0 or value > 100:
            raise ValueError("Volume must be between 0 and 100")        
        value = int(value / 100 * DFPLAYER_MAX_VOLUME) # Map to range 0 - 30
        self._exec_command(DFPLAYER_CMD_SET_VOLUME, 0x00, value)

    def play_track(self, folder, track):
        """Play the given track number from the given folder."""
        if folder < 0 or folder > DFPLAYER_MAX_FOLDER:
            raise ValueError("Folder number must be between 0 and 99")
        if track < 0 or track > DFPLAYER_MAX_MP3_FILE:
            raise ValueError("Track number must be between 0 and 255")
        self._exec_command(DFPLAYER_CMD_FILE, folder, track, check_error=True)

    def play_track_by_number(self, track_number):
        """Play the given track number from the flattened file list."""
        self._exec_command(DFPLAYER_CMD_PLAY_TRACK, track_number >> 8, track_number & 0xFF)

    def play_from_advert_folder(self, track_number):
        """Play the given track number from the "ADVERT" folder."""
        if track_number < 0 or track_number > DFPLAYER_MAX_ADVERT_FILE:
            raise ValueError("Track number must be between 0 and 9999")
        self._send_command(DFPLAYER_CMD_PLAY_ADVERT, track_number >> 8, track_number & 0xFF)

    def enter_standby(self):
        """Enter or exit standby mode."""
        self._send_command(DFPLAYER_CMD_STANDBY_ENTER)

    @property
    def status(self) -> PlayerStatus:
        """
        Return the current status of the DFPlayer.
        The possible return values are:
        - PlayerStatus.STOPPED
        - PlayerStatus.PLAYING
        - PlayerStatus.PAUSED
        """
        response_data = self._exec_command(DFPLAYER_CMD_GET_STATUS, is_query=True).data
        
        if response_data == DFPLAYER_STATUS_STOPPED:
            return PlayerStatus.STOPPED
        if response_data == DFPLAYER_STATUS_PLAYING:
            return PlayerStatus.PLAYING
        if response_data == DFPLAYER_STATUS_PAUSED:
            return PlayerStatus.PAUSED
        
        return None

if __name__ == "__main__":
    from machine import UART
    from time import sleep_ms
    uart1 = UART(0, tx=Pin("TX"), rx=Pin("RX"))
    uart2 = UART(1, tx=Pin("D9"), rx=Pin("D8"))
    player1 = DFPlayer(uart1)
    player2 = DFPlayer(uart2)
    # player.reset()
    #busy_pin = Pin("D4")
    #player = DFPlayer(uart, busy_pin)
    # print(f"Status: {player.status}")
    # player.volume = 20
    # print(f"Volume: {player.volume}")
    # player.play() # Play the current / first track
    # sleep_ms(5000)
    # print("Pausing")
    # player.pause()
    # print(f"Status: {player.status}")
    # print("Playing")
    # player.play()
    # sleep_ms(1000)
    # print("Next track")
    # player.next_track()
    # sleep_ms(5000)
    # print("Next track")
    # player.next_track()
    # sleep_ms(5000)
    #player.play_track(2, 1) # Play track 1 from folder 2