# Author: Sebastian Romero

from micropython import const
from machine import Pin
from time import sleep_ms
import struct

# Macros
DFPLAYER_BOOTUP_TIME_MS = const(3000)  # Boot up of the device takes 1.5 to 3 secs.
DFPLAYER_TIMEOUT_MS = const(100)  # Timeout waiting for a replay in milliseconds.
DFPLAYER_SEND_DELAY_MS = const(100)  # Wait 100ms after a cmd to work around hw bug.
DFPLAYER_RETRIES = const(5)  # How often to retry a command on timeout.
DFPLAYER_MAX_VOLUME = const(30)  # Maximum supported volume.
DFPLAYER_MAX_FOLDER = const(99)  # Highest supported folder number.
DFPLAYER_MAX_MP3_FILE = const(9999)  # Highest supported file number in the "MP3" folder.
DFPLAYER_MAX_ADVERT_FILE = const(9999)  # Highest supported file number in the "ADVERT" folder.
DFPLAYER_LOWEST_QUERY = const(0x40)  # Query commands are 0x40 or higher.

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

# Commands supported by the DFPlayer Mini
DFPLAYER_CMD_NEXT = const(0x01)  # Start playing the next song.
DFPLAYER_CMD_PREV = const(0x02)  # Start playing the next song.
DFPLAYER_CMD_VOLUME_INC = const(0x04)  # Increase volume.
DFPLAYER_CMD_VOLUME_DEC = const(0x05)  # Decrease volume.
DFPLAYER_CMD_SET_VOLUME = const(0x06)  # Set the volume to the given level.
DFPLAYER_CMD_SET_EQUALIZER = const(0x07)  # Set the equalizer to the given setting.
DFPLAYER_CMD_SET_PLAYBACK_MODE = const(0x08)  # Set the playback mode.
DFPLAYER_CMD_SET_SOURCE = const(0x09)  # Set the source to play files from.
DFPLAYER_CMD_STANDBY_ENTER = const(0x0a)  # Enter low power mode.
DFPLAYER_CMD_STANDBY_EXIT = const(0x0b)  # Exit low power mode, back to normal mode.
DFPLAYER_CMD_RESET = const(0x0c)  # Reset the DFPlayer Mini.
DFPLAYER_CMD_PLAY = const(0x0d)  # Start playing the selected file.
DFPLAYER_CMD_PAUSE = const(0x0e)  # Pause the playback.
DFPLAYER_CMD_FILE = const(0x0f)  # Play the given file.
DFPLAYER_CMD_PLAY_FROM_MP3 = const(0x12)  # Play the given file (1-9999) from the folder "MP3"
DFPLAYER_CMD_PLAY_ADVERT = const(0x13)  # Play the given file (1-9999) from the folder "ADVERT", resume current playback afterwards.
DFPLAYER_CMD_ABORT_ADVERT = const(0x15)  # Play the given file (1-9999) from the folder "ADVERT", resume current playback afterwards.
DFPLAYER_CMD_REPEAT_FOLDER = const(0x17)  # Start repeat-playing the given folder (1-99)
DFPLAYER_CMD_RANDOM = const(0x18)  # Start playing all files in random order.
DFPLAYER_CMD_REPEAT = const(0x19)  # 0 = repeat currently played file, 1 = stop repeating
DFPLAYER_CMD_GET_STATUS = const(0x42)  # Retrieve the current status.
DFPLAYER_CMD_GET_VOLUME = const(0x43)  # Retrieve the current volume.
DFPLAYER_CMD_GET_EQUALIZER = const(0x44)  # Retrieve the current equalizer setting.
DFPLAYER_CMD_GET_MODE = const(0x45)  # Retrieve the current playback mode.
DFPLAYER_CMD_GET_VERSION = const(0x46)  # Retrieve the device's software version.
DFPLAYER_CMD_FILES_USB = const(0x47)  # Get the total number of files on USB storage.
DFPLAYER_CMD_FILES_SDCARD = const(0x48)  # Get the total number of files on the SD card.
DFPLAYER_CMD_FILES_FLASH = const(0x49)  # Get the total number of files on NOR flash.
DFPLAYER_CMD_FILENO_USB = const(0x4b)  # Get the currently select file number on the USB storage.
DFPLAYER_CMD_FILENO_SDCARD = const(0x4c)  # Get the currently select file number on the SD-Card.
DFPLAYER_CMD_FILENO_FLASH = const(0x4d)  # Get the currently select file number on the NOR flash.

# Classes of messages received from the DFPlayer
DFPLAYER_CLASS_MASK = const(0xf0)  # Use this mask to get the class from a response code.
DFPLAYER_CLASS_NOTIFY = const(0x30)  # Message is an event notification (unrelated to any command)
DFPLAYER_CLASS_RESPONSE = const(0x40)  # Message is a response to the most recent command.

# Notification codes sent by the DFPlayer Mini
DFPLAYER_NOTIFY_INSERT = const(0x3a)  # A USB storage device or an SD card was inserted.
DFPLAYER_NOTIFY_EJECT = const(0x3b)  # A USB storage device or an SD card was ejected.
DFPLAYER_NOTIFY_DONE_USB = const(0x3c)  # Completed playing the indicated track from USB storage.
DFPLAYER_NOTIFY_DONE_SDCARD = const(0x3d)  # Completed playing the indicated track from SD card.
DFPLAYER_NOTIFY_DONE_FLASH = const(0x3e)  # Completed playing the indicated track from flash.
DFPLAYER_NOTIFY_READY = const(0x3f)  # The DFPlayer is ready.

# Bitmasks identifying the playback sources in the ready notification
DFPLAYER_MASK_USB = const(0x01)  # USB stick is connected.
DFPLAYER_MASK_SDCARD = const(0x02)  # SD-Card is connected.
DFPLAYER_MASK_PC = const(0x04)  # Unclear, has something to do with debugging.
DFPLAYER_MASK_FLASH = const(0x08)  # NOR flash is connected.

# Response codes sent by the DFPlayer Mini
DFPLAYER_RESPONSE_ERROR = const(0x40)  # While processing the most recent command an error occurred.
DFPLAYER_RESPONSE_OK = const(0x41)  # Last command succeeded.

# Error codes sent as parameter of error messages
DFPLAYER_ERROR_BUSY = const(0x00)  # Module is busy.
DFPLAYER_ERROR_FRAME = const(0x01)  # Received incomplete frame.
DFPLAYER_ERROR_FCS = const(0x02)  # Frame check sequence of last frame didn't match.
DFPLAYER_ERROR_NO_SUCH_FILE = const(0x06)  # File/folder selected for playback (command 0x06) does not exit.

# Device identifiers in insert/eject notifications
DFPLAYER_DEVICE_USB = const(0x01)  # A USB storage device was inserted/ejected.
DFPLAYER_DEVICE_SDCARD = const(0x02)  # An SD card was inserted/ejected.

# Status bitmasks
DFPLAYER_STATUS_STOPPED = 0x00
DFPLAYER_STATUS_PLAYING = 0x01 # The DFPlayer is currently playing a song.
DFPLAYER_STATUS_PAUSED  = 0x02 # The DFPlayer is paused.

# Flags to store info about the driver state
DFPLAYER_FLAG_NO_ACK_BUG = const(0x01)  # The next command will be affected by the no-ACK bug.

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

class PlaybackMode:
    REPEAT = 0
    FOLDER_REPEAT = 1
    SINGLE_REPEAT = 2
    RANDOM = 3

class PlaybackSource:
    USB = 0
    SD_CARD = 1
    AUX = 2
    SLEEP = 3
    FLASH = 4

class DFPlayer:
    def __init__(self, uart, busy_pin = None):
        self.uart = uart
        uart.init(baudrate=DFPLAYER_BAUD, bits=DFPLAYER_DATA_BITS, parity=DFPLAYER_PARITY, stop=DFPLAYER_STOP_BITS)
        self.busy_pin = busy_pin
        if busy_pin:
            self.busy_pin.init(Pin.IN)
            busy_pin.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self._on_busy_pin_change)

    def _on_busy_pin_change(self, pin):
         # High level during playback; Low in pause status and module sleep
        self._playing = pin.value() == 0

    @property
    def playing(self):
        """Return True if the DFPlayer is currently playing a song."""
        if self.busy_pin: # If we have a busy pin, use it
            return self._playing
        return self.status == PlayerStatus.PLAYING

    def _read_data(self):        
        if not self.uart.any():
            return None, None
        
        buf = self.uart.read(DFPLAYER_FRAME_SIZE)
        if buf is None or len(buf) != DFPLAYER_FRAME_SIZE:
            return None, None        
        
        if buf[0] == DFPLAYER_START and buf[1] == DFPLAYER_VERSION and buf[2] == DFPLAYER_LEN and buf[9] == DFPLAYER_END:
            cmd = buf[3]
            data = struct.unpack('>H', buf[5:7])[0]
            return (cmd, data)
        
        # TODO: Handle invalid frames
        #return None
        raise RuntimeError("Invalid frame received")

    def _send_command(self, command, data_high = 0x0, data_low = 0x0):
        # Ensure command is only one byte long
        if command > 0xFF:
            raise ValueError("Command must be a single byte")
        frame_check_init = -(DFPLAYER_VERSION + DFPLAYER_LEN)
        checksum = frame_check_init - (command + DFPLAYER_ACK + data_low + data_high)
        high_byte, low_byte = checksum >> 8, checksum & 0xFF
        frame = [DFPLAYER_START, DFPLAYER_VERSION, DFPLAYER_LEN, command, DFPLAYER_ACK, data_high, data_low, high_byte, low_byte, DFPLAYER_END]        
        frame = bytes([b & 0xFF for b in frame]) # Convert to unsigned bytes
        self.uart.write(bytes(frame))
        
        # TODO extract into a method
        # Give device some time to process the command
        # TODO: Added DFPLAYER_CMD_SET_VOLUME. Check if only set volume needs more time or all commands
        # so we could bump DFPLAYER_SEND_DELAY_MS to 200ms
        if command in [DFPLAYER_CMD_SET_SOURCE, DFPLAYER_CMD_SET_VOLUME]: # set_media
            sleep_ms(200)
        elif command == DFPLAYER_CMD_RESET: # reset
            sleep_ms(DFPLAYER_BOOTUP_TIME_MS)
        elif command in [0x47,0x48,0x49,0x4E]:     # query files
            sleep_ms(500)
        else:
            sleep_ms(DFPLAYER_SEND_DELAY_MS) # other commands
        
        response_code, response_data = self._read_data()

        if response_code == DFPLAYER_RESPONSE_OK:
            return True
        
        if response_code == DFPLAYER_RESPONSE_ERROR:
            if response_data == DFPLAYER_ERROR_BUSY:
                raise RuntimeError("DFPlayer is busy")
            if response_data == DFPLAYER_ERROR_FRAME:
                raise RuntimeError("DFPlayer received incomplete frame")
            if response_data == DFPLAYER_ERROR_FCS:
                raise RuntimeError("DFPlayer received corrupted frame (FCS mismatch)")
            if response_data == DFPLAYER_ERROR_NO_SUCH_FILE:
                raise RuntimeError("No such file or folder")
            raise RuntimeError("Unknown error")          
        
    def reset(self):
        """Reset the DFPlayer."""
        self._send_command(DFPLAYER_CMD_RESET)

    def next_track(self):
        self._send_command(DFPLAYER_CMD_NEXT)
    
    def previous_track(self):
        self._send_command(DFPLAYER_CMD_PREV)

    def play(self):
        self._send_command(DFPLAYER_CMD_PLAY)

    def pause(self):
        self._send_command(DFPLAYER_CMD_PAUSE)

    @property
    def equalizer_settings(self):
        """Return the current equalizer setting."""
        self._send_command(DFPLAYER_CMD_GET_EQUALIZER)
        response_code, response_data = self._read_data()
        if response_code != DFPLAYER_CMD_GET_EQUALIZER:
            raise RuntimeError("Invalid response received")
        return response_data
    
    @equalizer_settings.setter
    def equalizer_settings(self, value: EqualizerMode):
        """Set the equalizer mode."""
        if value < 0 or value > 5:
            raise ValueError("Equalizer mode must be between 0 and 5")
        self._send_command(DFPLAYER_CMD_SET_EQUALIZER, 0x00, value)

    def increase_volume(self):
        self._send_command(DFPLAYER_CMD_VOLUME_INC)

    def decrease_volume(self):
        self._send_command(DFPLAYER_CMD_VOLUME_DEC)
    
    @property
    def volume(self):
        pass

    @volume.setter
    def volume(self, value : int):
        """Set the volume of the DFPlayer in percent (0-100%)."""
        if value < 0 or value > 100:
            raise ValueError("Volume must be between 0 and 100")        
        value = int(value / 100 * DFPLAYER_MAX_VOLUME) # Map to range 0 - 30
        self._send_command(DFPLAYER_CMD_SET_VOLUME, 0x00, value)

    def play_from_mp3_folder(self, track_number):
        """Play the given track number from the "MP3" folder."""
        if track_number < 0 or track_number > DFPLAYER_MAX_MP3_FILE:
            raise ValueError("Track number must be between 0 and 9999")
        self._send_command(DFPLAYER_CMD_PLAY_FROM_MP3, track_number & 0xFF, track_number >> 8)

    def play_track(self, folder, track):
        """Play the given track number from the given folder."""
        if folder < 0 or folder > DFPLAYER_MAX_FOLDER:
            raise ValueError("Folder number must be between 0 and 99")
        if track < 0 or track > DFPLAYER_MAX_MP3_FILE:
            raise ValueError("Track number must be between 0 and 9999")
        self._send_command(DFPLAYER_CMD_FILE, folder, track)

    def set_playback_mode(self, mode: PlaybackMode):
        """
        Set the playback mode (0 - 3). 
        0 = repeat, 1 = folder repeat, 2 = single repeat, 3 = random.
        """
        if mode < 0 or mode > 1:
            raise ValueError("Playback mode must be 0 or 1")
        self._send_command(DFPLAYER_CMD_SET_PLAYBACK_MODE, 0x00, mode)

    def set_playback_source(self, source : PlaybackSource):
        """
        Set the playback source.
        0 = U-disk, 1 = SD card, 2 = AUX, 3 = SLEEP, 4 = FLASH
        """
        if source < 0 or source > 4:
            raise ValueError("Playback source must be between 0 and 4")
        self._send_command(DFPLAYER_CMD_SET_SOURCE, 0x00, source)

    def set_standby(self, enabled : bool):
        """Enter or exit standby mode."""
        if enabled:
            self._send_command(DFPLAYER_CMD_STANDBY_ENTER)
        else:
            self._send_command(DFPLAYER_CMD_STANDBY_EXIT)

    @property
    def status(self) -> PlayerStatus:
        """
        Return the current status of the DFPlayer.
        The possible return values are:
        - PlayerStatus.STOPPED
        - PlayerStatus.PLAYING
        - PlayerStatus.PAUSED
        """
        self._send_command(DFPLAYER_CMD_GET_STATUS)
        response_code, response_data = self._read_data()
        if response_code != DFPLAYER_CMD_GET_STATUS:
            raise RuntimeError(f"Invalid response code received {response_code}")
        
        if response_data == DFPLAYER_STATUS_STOPPED:
            return PlayerStatus.STOPPED
        if response_data == DFPLAYER_STATUS_PLAYING:
            return PlayerStatus.PLAYING
        if response_data == DFPLAYER_STATUS_PAUSED:
            return PlayerStatus.PAUSED
        
        return None

if __name__ == "__main__":
    from machine import UART
    uart = UART(0, tx=Pin("TX"), rx=Pin("RX"))
    player = DFPlayer(uart)
    #busy_pin = Pin("D4")
    #player = DFPlayer(uart, busy_pin)
    #print(player.status)
    player.volume = 20
    #player.play() # Play the current / first track
    #player.play_track(2, 1) # Play track 1 from folder 2