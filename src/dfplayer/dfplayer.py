# Author: Sebastian Romero

from micropython import const, schedule
from machine import Pin, UART
from time import sleep_ms, ticks_ms
import struct
from collections import deque

# CONFIG
_DFPLAYER_BOOTUP_TIME_MS = const(3000)  # Boot up of the device takes 1.5 to 3 secs.
_DFPLAYER_TIMEOUT_UART_MS = const(100)  # Default timeout waiting for UART data in milliseconds.

_DFPLAYER_MAX_VOLUME = const(30)  # Maximum supported volume.
_DFPLAYER_MAX_FOLDER = const(99)  # Highest supported folder number.
_DFPLAYER_MAX_FILE = const(255)  # Highest supported file number in the "MP3" folder.
_DFPLAYER_MAX_MP3_FILE = const(65536)  # Highest supported file number in the "MP3" folder.
_DFPLAYER_MAX_ADVERT_FILE = const(65536)  # Highest supported file number in the "ADVERT" folder.

# Constants used in frames sent to the DFPlayer Mini
_DFPLAYER_FRAME_SIZE = const(10)  # Size of a frame sent to the DFPlayer Mini.
_DFPLAYER_START = const(0x7e)  # Start symbol.
_DFPLAYER_VERSION = const(0xff)  # Value to use in version field.
_DFPLAYER_LEN = const(0x06)  # Length of a frame. (Command length)
_DFPLAYER_NO_ACK = const(0x00)  # No acknowledgement of CMD required.
_DFPLAYER_ACK = const(0x01)  # Acknowledgement of CMD required.
_DFPLAYER_END = const(0xef)  # End symbol.

# UART settings of the DFPlayer Mini
_DFPLAYER_BAUD = const(9600)  # Symbol rate of the DFPlayer mini.
_DFPLAYER_DATA_BITS = const(8)  # The DFPlayer uses 8 data bits.
_DFPLAYER_PARITY = const(None)  # The DFPlayer does not use a parity bit.
_DFPLAYER_STOP_BITS = const(1)  # The DFPlayer uses 1 stop bit.

# Classes of messages received from the DFPlayer
_DFPLAYER_CLASS_MASK = const(0xf0)  # Use bits 4-7 to get the class from a response code.
_DFPLAYER_CLASS_NOTIFY = const(0x30)  # Message is an event notification (unrelated to any command)

# Notification codes
# Note: Done frames contain the track number in the data field
_DFPLAYER_NOTIFY_INSERT = const(0x3a)  # A USB storage device or an SD card was inserted.
_DFPLAYER_NOTIFY_EJECT = const(0x3b)  # A USB storage device or an SD card was ejected.
_DFPLAYER_NOTIFY_DONE_USB = const(0x3c)  # Completed playing the indicated track from USB storage.
_DFPLAYER_NOTIFY_DONE_SDCARD = const(0x3d)  # Completed playing the indicated track from SD card.
_DFPLAYER_NOTIFY_DONE_FLASH = const(0x3e)  # Completed playing the indicated track from flash.
_DFPLAYER_NOTIFY_INIT = const(0x3f)  # Ready notification after initialization.

# Device identifiers in insert/eject notifications
DFPLAYER_DEVICE_USB = const(0x01)  # A USB storage device was inserted/ejected.
DFPLAYER_DEVICE_SDCARD = const(0x02)  # An SD card was inserted/ejected.

# Bitmasks identifying the playback sources in the ready notification
DFPLAYER_SOURCE_USB = const(0x01)  # USB stick is connected.
DFPLAYER_SOURCE_SDCARD = const(0x02)  # SD-Card is connected.
DFPLAYER_SOURCE_USB_SDCARD = const(0x03)  # Both USB stick and SD-Card are connected.
DFPLAYER_SOURCE_PC = const(0x04)  # Unclear, has something to do with debugging.
DFPLAYER_SOURCE_FLASH = const(0x08)  # NOR flash is connected.

# Status bitmasks
_DFPLAYER_STATUS_MASK = const(0x0f)  # Use bits 0-3 to get the status from a response code.
_DFPLAYER_STATUS_STOPPED = const(0x00) # The DFPlayer is currently stopped e.g. done playing a song.
_DFPLAYER_STATUS_PLAYING = const(0x01) # The DFPlayer is currently playing a song.
_DFPLAYER_STATUS_PAUSED  = const(0x02) # The DFPlayer is paused.

# Response codes sent by the DFPlayer
_DFPLAYER_RESPONSE_ERROR = const(0x40)  # While processing the most recent command an error occurred.
_DFPLAYER_RESPONSE_ACK = const(0x41)  # Last command succeeded.

# Error codes sent as parameter of error messages
# Warning: The documentation of DFRobot's DFPlayer seems to be wrong/incomplete here
_DFPLAYER_ERROR_BUSY = const(0x01)  # Module is busy (initialization not done).
_DFPLAYER_ERROR_SLEEPING = const(0x02)  # Module is in sleep mode (only on specific devices).
_DFPLAYER_ERROR_FRAME = const(0x03)  # Received incomplete frame over UART.
_DFPLAYER_ERROR_FCS = const(0x04)  # Checksum of last frame incorrect.
_DFPLAYER_ERROR_OUT_OF_RANGE = const(0x05)  # Requested track/folder is out of range.
_DFPLAYER_ERROR_NO_SUCH_FILE = const(0x06)  # File/folder selected for playback (command 0x06) does not exist.
_DFPLAYER_ERROR_INSERTION_CMD = const(0x07)  # inserting operation only can be donewhen a track is being played
_DFPLAYER_ERROR_SD_READ = const(0x08)  # SD-card reading failed (SD-card pulled out or damaged).
_DFPLAYER_ERROR_SLEEP_MODE = const(0x0A)  # Error while entering sleep mode (only on specific devices).

# Common Commands
_DFPLAYER_CMD_NEXT = const(0x01)  # Start playing the next song.
_DFPLAYER_CMD_PREV = const(0x02)  # Start playing the next song.
_DFPLAYER_CMD_PLAY_TRACK = const(0x03)  # Play the given track. (DFROBOT: 0-2999) (MH2024/GD3200: 0-65535)
_DFPLAYER_CMD_VOLUME_INC = const(0x04)  # Increase volume.
_DFPLAYER_CMD_VOLUME_DEC = const(0x05)  # Decrease volume.
_DFPLAYER_CMD_SET_VOLUME = const(0x06)  # Set the volume to the given level. (0-30)
_DFPLAYER_CMD_SET_EQUALIZER = const(0x07)  # Set the equalizer to the given setting. (0-5)
_DFPLAYER_CMD_SINGLE_TRACK_LOOP = const(0x08)  # Loops single track (0-65535) (Also on DFRobot's DFPlayer)
_DFPLAYER_CMD_SET_SOURCE = const(0x09)  # Set the source to play files from.
_DFPLAYER_CMD_STANDBY_ENTER = const(0x0a)  # Enter low power mode.
_DFPLAYER_CMD_RESET = const(0x0c)  # Reset the DFPlayer Mini.
_DFPLAYER_CMD_PLAY = const(0x0d)  # Start playing the selected file.
_DFPLAYER_CMD_PAUSE = const(0x0e)  # Pause the playback.
_DFPLAYER_CMD_PLAY_FILE = const(0x0f)  # Play the given file (1-255) in the given folder (1-99)
_DFPLAYER_CMD_REPEAT_ALL = const(0x11)  # Start/stop repeat-playing the whole source. 1=loop 0=stop
_DFPLAYER_CMD_PLAY_FROM_MP3 = const(0x12)  # Play the given file (1-9999) from the folder "MP3"
_DFPLAYER_CMD_PLAY_ADVERT = const(0x13)  # Play the given file (1-9999) from the folder "ADVERT", resume current playback afterwards.
_DFPLAYER_CMD_FILE_LARGE = const(0x14)  # Play the given file (1-4095) in the given folder (1-15).
_DFPLAYER_CMD_ABORT_ADVERT = const(0x15)  # Abort advert playback and resume current playback.
_DFPLAYER_CMD_STOP = const(0x16)  # Stop playback.
_DFPLAYER_CMD_REPEAT_FOLDER = const(0x17)  # Start repeat-playing the given folder (1-99)
_DFPLAYER_CMD_RANDOM = const(0x18)  # Start playing all files in random order.
_DFPLAYER_CMD_MUTE = const(0x1a)  # Mute/unmute the audio output. 0=unmute, 1=mute
_DFPLAYER_CMD_ADVERT_FOLDER = const(0x25) # Play from advert folder 1-9
_DFPLAYER_CMD_GET_STATUS = const(0x42)  # Retrieve the current status.
_DFPLAYER_CMD_GET_VOLUME = const(0x43)  # Retrieve the current volume.
_DFPLAYER_CMD_GET_EQUALIZER = const(0x44)  # Retrieve the current equalizer setting.
_DFPLAYER_CMD_GET_PLAYBACK_MODE = const(0x45)  # Retrieve the current playback mode.
_DFPLAYER_CMD_GET_VERSION = const(0x46)  # Retrieve the device's software version.

# Commands to query files
# Warning: The documentation of DFRobot's DFPlayer DFROBOT|LISP3 mixes up those commands
# It follows the documentation of the MH2024K/GD3200 instead
_DFPLAYER_CMD_FILES_USB = const(0x47)  # Get the total number of files on USB storage.
_DFPLAYER_CMD_FILES_SDCARD = const(0x48)  # Get the total number of files on the SD card.
_DFPLAYER_CMD_FILES_FLASH = const(0x49)  # Get the total number of files on the internal flash.
_DFPLAYER_CMD_FILENO_USB = const(0x4b)  # Get the currently select file number on the USB storage.
_DFPLAYER_CMD_FILENO_SDCARD = const(0x4c)  # Get the currently select file number on the SD-Card.    
_DFPLAYER_CMD_FILENO_FLASH = const(0x4d)  # Get the currently select file number on the NOR flash.
_DFPLAYER_CMD_FILES_IN_FOLDER = const(0x4e)  # Get the number of files in the current folder.
_DFPLAYER_CMD_FOLDERS = const(0x4f)  # Get the number of folders.

class Frame():
    def __init__(self, raw_data):
        if raw_data is None or len(raw_data) != _DFPLAYER_FRAME_SIZE:
            raise ValueError(f"Frame data must be exactly {_DFPLAYER_FRAME_SIZE} bytes")
        
        if raw_data[0] != _DFPLAYER_START:
            raise ValueError(f"Invalid frame start byte ({hex(raw_data[0])}) in frame: {self._frame_as_string(raw_data)}")

        if  raw_data[1] != _DFPLAYER_VERSION:
            raise ValueError(f"Invalid frame version byte ({hex(raw_data[1])}) in frame: {self._frame_as_string(raw_data)}")
        
        if raw_data[2] != _DFPLAYER_LEN:
            raise ValueError(f"Invalid frame length byte ({hex(raw_data[2])}) in frame: {self._frame_as_string(raw_data)}")
        
        if raw_data[9] != _DFPLAYER_END:
            raise ValueError(f"Invalid frame end byte ({hex(raw_data[9])}) in frame: {self._frame_as_string(raw_data)}")    

        self.command = raw_data[3]
        self.data = struct.unpack('>H', raw_data[5:7])[0]
        self.raw_data = raw_data

    def _frame_as_string(self, raw_data):
        return " ".join([hex(b) for b in raw_data])

    def __str__(self):
        return self._frame_as_string(self.raw_data)
    
    @property
    def is_notification(self):
        """Return True if the frame is a notification from the DFPlayer."""
        return (self.command & _DFPLAYER_CLASS_MASK) == _DFPLAYER_CLASS_NOTIFY
    
    @property
    def is_error(self):
        """Return True if the frame is an error response from the DFPlayer."""
        return self.command == _DFPLAYER_RESPONSE_ERROR
    
    @property
    def is_ack(self):
        """Return True if the frame is an ACK response from the DFPlayer."""
        return self.command == _DFPLAYER_RESPONSE_ACK

class FrameReader():
    def __init__(self, uart, use_irq = False):
        """
        Initialize the FrameReader.
        Parameters:
            uart (UART): The UART instance to read frames from.
            use_irq (bool): Whether to use IRQ for reading frames. Default is False.
                            Note: On ESP32 it uses Timer(0) which makes it unavailable for other uses.
        """
        self.uart = uart
        self._frames = deque([], 10)  # Store up to 10 frames
        self._on_notification = None
        self._use_irq = use_irq
        
        if use_irq:        
            # IRQ_RXIDLE is not available on all ports (e.g. CC3200, NRF), use IRQ_RX in that case
            trigger_event = UART.IRQ_RXIDLE if hasattr(UART, 'IRQ_RXIDLE') else UART.IRQ_RX
            uart.irq(handler= lambda _: schedule(self._update_from_irq, None), trigger=trigger_event)

    def _read_frame(self, timeout_ms = 1000) -> Frame | None:
        if self.uart.any() == 0:
            # No data available
            return None

        start_time = ticks_ms()

        while True:
            if timeout_ms is not None and (ticks_ms() - start_time) >= timeout_ms:
                return None
            
            next_byte = self.uart.read(1)
            if next_byte is None:
                sleep_ms(10)
                continue
            if next_byte[0] == _DFPLAYER_START:
                break
            else:
                print(f"Discarding spurious byte: {hex(next_byte[0])}")

        # Wait for the rest of the frame
        while self.uart.any() < _DFPLAYER_FRAME_SIZE - 1:
            if timeout_ms is not None and (ticks_ms() - start_time) >= timeout_ms:
                return None
            sleep_ms(10)

        data = self.uart.read(_DFPLAYER_FRAME_SIZE - 1)  # Read the rest of the frame
        return Frame(bytes([_DFPLAYER_START]) + data)

    def set_notification_callback(self, callback : callable):
        self._on_notification = callback

    def clear(self):
        """Clear all frames from the internal buffer."""
        while len(self._frames) > 0:
            f = self._frames.popleft()
            print(f"DEBUG: Discarding frame during clear. Code: {hex(f.command)} Data: {hex(f.data)}")

    def _update_from_irq(self, _):
        """
        Updates the frame buffer from UART triggered by IRQ as soon as data is available.        
        This function is scheduled from the IRQ handler and does not run in IRQ context.
        """
        if self.uart.any() >= _DFPLAYER_FRAME_SIZE:
            self._process_frames()

    def _process_frames(self, await_frames = 0, timeout_ms = 1000) -> int:
        """
        Read frames from the UART and store them in the internal buffer.
        If await_frames > 0, wait until at least that many frames are available or timeout occurs.
        If timeout_ms is None, wait indefinitely.
        
        Parameters:
            await_frames (int): Number of frames to wait for before returning. Default is 0 (no wait).
            timeout_ms (int | None): Maximum time to wait in milliseconds. None means wait indefinitely

        Returns:
            int: Number of frames added to the internal buffer during this call.
        """
        start_time = ticks_ms()
        frames_added = 0

        while True:
            # Check for timeout
            if timeout_ms is not None and (ticks_ms() - start_time) >= timeout_ms:
                return frames_added
                        
            f = self._read_frame()
            if f is None:
                # Wait until we have at least requested amount of frames
                if len(self._frames) < await_frames:
                    sleep_ms(10)
                    continue
                return frames_added
            if f.is_notification:
                if self._on_notification:
                    self._on_notification(f)
                # Notifications are not stored in the buffer
                continue
            self._frames.append(f)
            frames_added += 1

    def update(self, await_frames = 0, timeout_ms = 1000) -> int:
        """
        Ensures that at least requested amount of frames are available in the internal buffer.
        If await_frames > 0, wait until at least that many frames are available or timeout occurs.
        If timeout_ms is None, wait indefinitely.
        If await_frames is 0, process available frames without waiting (timeout does not apply).
        In IRQ mode, frames are read in the IRQ handler hence this function always returns 0.
        """
        if self._use_irq:
            start_time = ticks_ms()
            while True:
                timeout_elapsed = timeout_ms is not None and (ticks_ms() - start_time) >= timeout_ms
                frequested_frames_received = len(self._frames) >= await_frames
                
                if timeout_elapsed or frequested_frames_received:
                    break
                sleep_ms(10) # Give some time for IRQ handler to process incoming data
                    
            return 0 # In IRQ mode, frames are read in the IRQ handler
        return self._process_frames(await_frames, timeout_ms)
            
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

class PlayerStatus:
    # Arbitrary values representing player status
    STOPPED = 0
    PLAYING = 1
    PAUSED = 2

class EqualizerMode:
    # These numbers directly map to 
    # the DFPlayer equalizer settings
    NORMAL = 0
    POP = 1
    ROCK = 2
    JAZZ = 3
    CLASSIC = 4
    BASS = 5 # Seems unsupported on DFRobot's DFPlayer

class DFPlayer:    
    def __init__(self, uart, busy_pin = None, use_irq = False):
        self.uart = uart
        uart.init(baudrate=_DFPLAYER_BAUD, bits=_DFPLAYER_DATA_BITS, parity=_DFPLAYER_PARITY, stop=_DFPLAYER_STOP_BITS, timeout=_DFPLAYER_TIMEOUT_UART_MS)
        self.busy_pin = busy_pin
        if busy_pin:
            self.busy_pin.init(Pin.IN)
            busy_pin.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self._on_busy_pin_change)
        
        self._frame_reader = FrameReader(uart, use_irq=use_irq)
        self._frame_reader.set_notification_callback(self._handle_notification)

        self._on_track_finished = None
        self._on_media_inserted = None
        self._on_media_ejected = None
        self._on_device_ready = None

    def _handle_notification(self, frame):
        cmd = frame.command
        if cmd == _DFPLAYER_NOTIFY_INIT:
            self._on_device_ready(frame.data) if self._on_device_ready else None
        elif cmd == _DFPLAYER_NOTIFY_INSERT:
            self._on_media_inserted(frame.data) if self._on_media_inserted else None
        elif cmd == _DFPLAYER_NOTIFY_EJECT:
            self._on_media_ejected(frame.data) if self._on_media_ejected else None
        elif cmd in [_DFPLAYER_NOTIFY_DONE_USB, _DFPLAYER_NOTIFY_DONE_SDCARD, _DFPLAYER_NOTIFY_DONE_FLASH]:
            # We consolidate all "done" notifications into a single callback
            # since only one source can be active at a time anyway.
            self._on_track_finished(frame.data) if self._on_track_finished else None

    def _on_busy_pin_change(self, pin):
         # High level during playback; Low in pause status and module sleep
        self._playing = pin.value() == 0

    def _calculate_checksum(self, command, data_high, data_low, ack):
        frame_check_init = -(_DFPLAYER_VERSION + _DFPLAYER_LEN)
        ack_flag = _DFPLAYER_ACK if ack else _DFPLAYER_NO_ACK
        checksum = frame_check_init - (command + ack_flag + data_low + data_high)
        return checksum >> 8, checksum & 0xFF

    def _send_command(self, command, data_high = 0x0, data_low = 0x0, ack = True):
        # Ensure command is only one byte long
        if command > 0xFF:
            raise ValueError("Command must be a single byte")
        if data_high > 0xFF or data_low > 0xFF:
            raise ValueError("Data high and low must be single byte values")
        ack_flag = _DFPLAYER_ACK if ack else _DFPLAYER_NO_ACK
        fcs_high, fcs_low = self._calculate_checksum(command, data_high, data_low, ack)
        frame = [_DFPLAYER_START, _DFPLAYER_VERSION, _DFPLAYER_LEN, command, ack_flag, data_high, data_low, fcs_high, fcs_low, _DFPLAYER_END]        
        frame = bytes([b & 0xFF for b in frame]) # Convert to unsigned bytes
        self.uart.write(bytes(frame))
        self.uart.flush() # Wait until all data is sent        

    def _handle_error_response(self, response_data):
        if response_data == _DFPLAYER_ERROR_NO_SUCH_FILE:
            raise RuntimeError("No such file or folder")
        if response_data == _DFPLAYER_ERROR_BUSY:
            raise RuntimeError("DFPlayer is busy")
        if response_data == _DFPLAYER_ERROR_FRAME:
            raise RuntimeError("DFPlayer received incomplete frame")
        if response_data == _DFPLAYER_ERROR_FCS:
            raise RuntimeError("DFPlayer received corrupted frame (FCS mismatch)")
        if response_data == _DFPLAYER_ERROR_OUT_OF_RANGE:
            raise RuntimeError("Requested track or folder is out of range")
        if response_data == _DFPLAYER_ERROR_SD_READ:
            raise RuntimeError("SD-card reading failed (SD-card pulled out or damaged)")
        if response_data == _DFPLAYER_ERROR_SLEEP_MODE:
            raise RuntimeError("Error while entering sleep mode")
        if response_data == _DFPLAYER_ERROR_SLEEPING:
            raise RuntimeError("Module is in sleep mode")
        if response_data == _DFPLAYER_ERROR_INSERTION_CMD:
            raise RuntimeError("Insertion operation can only be done when a track is being played")
        raise RuntimeError(f"Unknown error. Data: {hex(response_data)}")          

    def _exec_command(self, command, data_high = 0x0, data_low = 0x0, ack = True, is_query = False, check_error = False):
        """
        Execute a command on the DFPlayer module.

        Parameters:
            command (int): The command byte to send.
            data_high (int): The high byte of the command data (default: 0x00).
            data_low (int): The low byte of the command data (default: 0x00).
            ack (bool): Whether to wait for an ACK response from the DFPlayer (default: True).
            is_query (bool): Whether the command is a query that expects a response containing data (default: False).
            check_error (bool): Whether to check for an error response after executing the command (default: False). 
                If True, the function will wait for an error response and raise an exception if an error is received.
        """
        # There shouldn't be any pending frames when sending a new command
        # however, if a response was received after the previous command timed out, it might be still in the buffer
        self._frame_reader.update()
        self._frame_reader.clear()

        self._send_command(command, data_high, data_low, ack)
        cmd_response = None
        
        # For queries it seems that first the query response is sent, then the ACK/ERROR response.
        if is_query:
            self._frame_reader.update(await_frames=1)
            # print(f"Amount of frames available (query): {self._frame_reader.available_frames()}")
            cmd_response = self._frame_reader.pop_frame()
            if cmd_response is None:
                # No response received for query
                return None

            if cmd_response.command != command:
                raise RuntimeError(f"Invalid response code. Expected: {hex(command)}, received: {hex(cmd_response.command)}, data: {hex(cmd_response.data)}")

        if ack:
            self._frame_reader.update(await_frames=1)
            # print(f"Amount of frames available (ack): {self._frame_reader.available_frames()}")
            ack_response = self._frame_reader.pop_frame()
            if not ack_response:
                raise RuntimeError(f"Command {hex(command)} was not acknowledged.")
            elif not ack_response.is_ack:
                raise RuntimeError(f"Received non-ack message for command {hex(command)}. Code: {hex(ack_response.command)} data: {hex(ack_response.data)}")

        if not check_error:
            return cmd_response

        # The following handles errors for execution commands such as play_track
        # Error response should be received within a short time
        # Increase the timeout to ~1000ms to account for edge cases
        # e.g. when executing play_track(1,123) while inserting an SD card
        # and the track does not exist, it takes roughly 1s to respond with the error.
        self._frame_reader.update(await_frames=1, timeout_ms=200)
        error_response = self._frame_reader.pop_frame()
        
        if error_response and error_response.is_error:
            self._handle_error_response(error_response.data)

        return cmd_response

    def on_track_finished(self, callback):
        """Register a callback to be called when a track finishes playing."""
        self._on_track_finished = callback

    def on_media_inserted(self, callback):
        """Register a callback to be called when media is inserted."""
        self._on_media_inserted = callback

    def on_media_ejected(self, callback):
        """Register a callback to be called when media is ejected."""
        self._on_media_ejected = callback

    def on_device_ready(self, callback):
        """Register a callback to be called when the device is ready after initialization."""
        self._on_device_ready = callback

    def update(self):
        """Update the internal frame reader to process incoming frames."""
        self._frame_reader.update()

    def reset(self):
        """Reset the DFPlayer."""
        self._exec_command(_DFPLAYER_CMD_RESET)
        sleep_ms(_DFPLAYER_BOOTUP_TIME_MS)
        # Reset command seems to generate spurious data in the UART buffer
        spurious_data = self.uart.any() % _DFPLAYER_FRAME_SIZE
        if spurious_data > 0:
            # print(f"Clearing {spurious_data} bytes of spurious data from UART buffer after reset")
            self.uart.read(spurious_data)
        
    def next_track(self):
        self._exec_command(_DFPLAYER_CMD_NEXT)
    
    def previous_track(self):
        self._exec_command(_DFPLAYER_CMD_PREV)

    def play(self):
        self._exec_command(_DFPLAYER_CMD_PLAY)

    def pause(self):
        self._exec_command(_DFPLAYER_CMD_PAUSE)

    def stop(self):
        self._exec_command(_DFPLAYER_CMD_STOP)

    def set_muted(self, muted : bool):
        """Mute or unmute the DFPlayer."""
        value = 0x01 if muted else 0x00
        self._exec_command(_DFPLAYER_CMD_MUTE, 0x00, value)

    def increase_volume(self):
        self._exec_command(_DFPLAYER_CMD_VOLUME_INC)

    def decrease_volume(self):
        self._exec_command(_DFPLAYER_CMD_VOLUME_DEC)
    
    def play_track(self, folder, track):
        """Play the given track number from the given folder."""
        if folder < 1 or folder > _DFPLAYER_MAX_FOLDER:
            raise ValueError("Folder number must be between 1 and 99")
        if track < 1 or track > _DFPLAYER_MAX_FILE:
            raise ValueError("Track number must be between 1 and 255")
        self._exec_command(_DFPLAYER_CMD_PLAY_FILE, folder, track, check_error=True)

    def play_track_by_number(self, track_number):
        """
        Play the given track number from the flattened file list.
        The order of tracks is determined by the underlying file table.
        """
        if track_number < 1 or track_number > 65535:
            raise ValueError("Track number must be between 1 and 65535")
        self._exec_command(_DFPLAYER_CMD_PLAY_TRACK, track_number >> 8, track_number & 0xFF, check_error=True)

    def play_from_mp3_folder(self, track_number):
        """Play the given track number (0001-65535) from the "MP3" folder."""
        if track_number < 0 or track_number > _DFPLAYER_MAX_MP3_FILE:
            raise ValueError("Track number must be between 0 and 9999")
        self._exec_command(_DFPLAYER_CMD_PLAY_FROM_MP3, track_number >> 8, track_number & 0xFF, check_error=True)

    def play_from_advert_folder(self, track_number):
        """
        Play the given track number from the "ADVERT" folder.
        On DFRobot's DFPlayer: Raises _DFPLAYER_ERROR_INSERTION_CMD if playback is not active.
        On MH2024K/GD3200: Resumes playback afterwards no matter if playback was active or not.
        """
        if track_number < 1 or track_number > _DFPLAYER_MAX_ADVERT_FILE:
            raise ValueError("Track number must be between 1 and 9999")
        self._exec_command(_DFPLAYER_CMD_PLAY_ADVERT, track_number >> 8, track_number & 0xFF, check_error=True)

    def play_from_custom_advert_folder(self, folder: int, track: int):
        """
        Play a track from the custom advert folder (1-9).
        The advert folder is a special folder that can be used to store short audio clips.
        The structure should be e.g. ADVERT2/001-Beep.mp3
        Starts/resumes playback after advertisment is done.
        """
        if folder < 1 or folder > 9:
            raise ValueError("Advert folder number must be between 1 and 9")
        if track < 1 or track > 255:
            raise ValueError("Track number must be between 1 and 255")
        self._exec_command(_DFPLAYER_CMD_ADVERT_FOLDER, folder, track, check_error=True)

    def play_random(self):
        """Start playing all tracks from the current source in random order."""
        self._exec_command(_DFPLAYER_CMD_RANDOM)

    def play_file_large(self, folder: int, file: int):
        """
        Play the given file (1-4095) in the given folder (1-15).
        This is for use cases where the file number exceeds 255 and cannot 
        be specified with the regular play_file command.

        Parameters:
            folder (int): The folder number (1-15)
            file (int): The file number (1-4095)
        """
        if folder < 1 or folder > 15:
            raise ValueError("Folder number must be between 1 and 15")
        if file < 1 or file > 4095:
            raise ValueError("File number must be between 1 and 4095")
        
        # The high 4 bytes represent the folder name
        # The low 12 bytes represent the file name
        data = ((folder & 0x0F) << 12) | (file & 0x0FFF)
        self._exec_command(_DFPLAYER_CMD_FILE_LARGE, (data >> 8) & 0xFF, data & 0xFF, check_error=True)

    def abort_advert(self):
        """Abort advert playback and resume current playback."""
        self._exec_command(_DFPLAYER_CMD_ABORT_ADVERT)

    def loop_track(self, track_id):
        """
        Loop the given track ID (0-65535) indefinitely. Starts playback.
        The index is the file number from the flattened file list sorted chronologically.
        It's the same as play_track_by_number but enables single track loop mode.
        """
        self._exec_command(_DFPLAYER_CMD_SINGLE_TRACK_LOOP, track_id >> 8, track_id & 0xFF, check_error=True)

    def repeat_all(self, repeat: bool = True):
        """
        Starts repeat playback of all files from the flattened file list in chronological order.
        If repeat is False, stops repeat playback and stops playback.

        Parameters:
            repeat (bool): True (default) to enable repeat all, False to disable.
        """
        value = 0x01 if repeat else 0x00
        self._exec_command(_DFPLAYER_CMD_REPEAT_ALL, 0x00, value)

    def repeat_folder(self, folder: int):
        """
        Start repeat-playing the given folder (1-99)        
        Tracks are played in the order they were added to the file table.
        """
        if folder < 1 or folder > _DFPLAYER_MAX_FOLDER:
            raise ValueError("Folder number must be between 1 and 99")
        self._exec_command(_DFPLAYER_CMD_REPEAT_FOLDER, 0x0, folder)

    def enter_standby(self):
        """Enter standby mode."""
        self._exec_command(_DFPLAYER_CMD_STANDBY_ENTER)

    def set_playback_source(self, source : int):
        """
        Set the playback source.
        USB disk, SD card, AUX, SLEEP, FLASH (not all variants support all sources).
        Parameters:
            source (int): Source identifier as per DFPlayer documentation (depending on variant).            
        """
        # According to the datasheet, this command takes 200ms
        self._exec_command(_DFPLAYER_CMD_SET_SOURCE, 0x00, source)

    @property
    def status(self) -> PlayerStatus | None:
        """
        Return the current status of the DFPlayer.
        The possible return values are:
        - PlayerStatus.STOPPED
        - PlayerStatus.PLAYING
        - PlayerStatus.PAUSED
        """
        response = self._exec_command(_DFPLAYER_CMD_GET_STATUS, is_query=True)
        if response is None:
            return None
        
        # MSB contains the source of the playback (USB/SD/Sleep), not available on all versions
        response_data = response.data & _DFPLAYER_STATUS_MASK
        
        if response_data == _DFPLAYER_STATUS_STOPPED:
            return PlayerStatus.STOPPED
        if response_data == _DFPLAYER_STATUS_PLAYING:
            return PlayerStatus.PLAYING
        if response_data == _DFPLAYER_STATUS_PAUSED:
            return PlayerStatus.PAUSED
        
        raise RuntimeError(f"Unknown status code received: {hex(response_data)}")

    @property
    def playing(self):
        """Return True if the DFPlayer is currently playing a song."""
        if self.busy_pin: # If we have a busy pin, use it
            return self._playing
        return self.status == PlayerStatus.PLAYING
    
    @property
    def volume(self) -> int | None:
        response = self._exec_command(_DFPLAYER_CMD_GET_VOLUME, is_query=True)
        return int(response.data / _DFPLAYER_MAX_VOLUME * 100) if response else None

    @volume.setter
    def volume(self, value : int):
        """Set the volume of the DFPlayer in percent (0-100%)."""
        if value < 0 or value > 100:
            raise ValueError("Volume must be between 0 and 100")        
        value = int(value / 100 * _DFPLAYER_MAX_VOLUME) # Map to range 0 - 30
        self._exec_command(_DFPLAYER_CMD_SET_VOLUME, 0x00, value)

    @property
    def equalizer_mode(self):
        """Return the current equalizer setting."""
        response_data = self._exec_command(_DFPLAYER_CMD_GET_EQUALIZER, is_query=True).data
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
        self._exec_command(_DFPLAYER_CMD_SET_EQUALIZER, 0x00, value)

    @property
    def software_version(self) -> int | None:
        """Return the DFPlayer software version as a number."""
        response = self._exec_command(_DFPLAYER_CMD_GET_VERSION, is_query=True)
        return response.data if response else None
    
    @property
    def playback_mode(self) -> int | None:
        """
        Return the current playback mode:
        Full cycle | Single cycle | Folder loop | 
        Random loop | Play the single once | Single seamless loop
        The meaning of the return values is device-dependent.
        """
        response = self._exec_command(_DFPLAYER_CMD_GET_PLAYBACK_MODE, is_query=True)
        return response.data if response else None
    
    @property
    def file_count_flash(self) -> int | None:
        """Return the total number of files on the internal flash storage."""
        response = self._exec_command(_DFPLAYER_CMD_FILES_FLASH, is_query=True)
        return response.data if response else None
    
    @property
    def file_count_usb(self) -> int | None:
        """Return the number of files on the USB storage."""
        response = self._exec_command(_DFPLAYER_CMD_FILES_USB, is_query=True)
        return response.data if response else None
    
    @property
    def file_count_sdcard(self) -> int | None:
        """Return the number of files on the SD card."""
        response = self._exec_command(_DFPLAYER_CMD_FILES_SDCARD, is_query=True)
        return response.data if response else None    
    
    def file_count_in_folder(self, folder: int) -> int | None:
        """Return the number of files in the given folder."""
        # Don't ask for an ACK message, since on DFROBOT|LISP3 the device responds 
        # with an ACK message first followed by the query response
        # wich is in reverse order compared to other queries. 
        # This is a workaround to avoid having to handle this special case in the main query handling code.
        # TODO: Check if we can handle this better by improving the query handling code
        # TODO: Error handling is not working for this command, since also the error response gets sent before the query response.
        response = self._exec_command(_DFPLAYER_CMD_FILES_IN_FOLDER, 0x00, folder, is_query=True, ack=False, check_error=True)
        return response.data if response else None

    @property
    def folder_count(self) -> int | None:
        """Return the number of folders on the current storage device."""
        # Don't ask for an ACK message, since on DFROBOT|LISP3 the device responds 
        # with an ACK message first followed by the query response
        # wich is in reverse order compared to other queries. 
        # This is a workaround to avoid having to handle this special case in the main query handling code.
        # TODO: Check if we can handle this better by improving the query handling code
        response = self._exec_command(_DFPLAYER_CMD_FOLDERS, is_query=True, ack=False)
        return response.data if response else None

    @property
    def current_file_number_sdcard(self) -> int | None:
        """
        Return the currently selected file number on the SD card.
        This number is the same as the track number used in play_track_by_number().
        """
        response = self._exec_command(_DFPLAYER_CMD_FILENO_SDCARD, is_query=True)
        return response.data if response else None
    
    @property
    def current_file_number_usb(self) -> int | None:
        """Return the currently selected file number on the USB storage."""
        response = self._exec_command(_DFPLAYER_CMD_FILENO_USB, is_query=True)
        return response.data if response else None
    
    @property
    def current_file_number_flash(self) -> int | None:
        """Return the currently selected file number on the internal flash storage."""
        response = self._exec_command(_DFPLAYER_CMD_FILENO_FLASH, is_query=True)
        return response.data if response else None
    