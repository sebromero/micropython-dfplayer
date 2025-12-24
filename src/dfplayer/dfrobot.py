from micropython import const
from .dfplayer import DFPlayer, DFPLAYER_CMD_PLAY_TRACK, DFPLAYER_CMD_SET_SOURCE

# TODO Depends on device. test
DFPLAYER_SEND_DELAY_MS = const(100)  # Wait 100ms after a cmd to work around hw bug.    
DFPLAYER_CMD_SET_PLAYBACK_MODE = const(0x08)  # Set the playback mode. (0-3)
DFPLAYER_CMD_STANDBY_EXIT = const(0x0b)  # Exit low power mode, back to normal mode.
DFPLAYER_CMD_VOLUME_ADJUST_SET = const(0x10) # TODO

DFPLAYER_CMD_FILES_SDCARD = const(0x47)  # Get the total number of files on the SD card.
DFPLAYER_CMD_FILES_USB = const(0x48)  # Get the total number of files on USB storage.
DFPLAYER_CMD_FILENO_SDCARD = const(0x4b)  # Get the currently select file number on the SD-Card.
DFPLAYER_CMD_FILENO_USB = const(0x4c)  # Get the currently select file number on the USB storage.
DFPLAYER_CMD_FILENO_FLASH = const(0x4d)  # Get the currently select file number on the NOR flash.

# Error codes sent as parameter of error messages
# TODO: Test as these are unverified
DFPLAYER_ERROR_BUSY = const(0x00)  # Module is busy.
DFPLAYER_ERROR_FRAME = const(0x01)  # Received incomplete frame.
DFPLAYER_ERROR_FCS = const(0x02)  # Frame check sequence of last frame didn't match.

class PlaybackSource:
    USB = 0
    SD_CARD = 1
    AUX = 2
    SLEEP = 3
    FLASH = 4

class PlaybackMode:
    REPEAT = 0
    FOLDER_REPEAT = 1
    SINGLE_REPEAT = 2
    RANDOM = 3

class DFRobotPlayer(DFPlayer):

    def play_track_by_number(self, track_number):
        """Play the given track number from the current folder"""
        if track_number < 0 or track_number > 2999:
            raise ValueError("Track number must be between 0 and 2999")            
        self._exec_command(DFPLAYER_CMD_PLAY_TRACK, 0x00, track_number)

    def exit_standby(self):
        """Exit low power mode, back to normal mode."""
        self._exec_command(DFPLAYER_CMD_STANDBY_EXIT)

    def set_playback_source(self, source : PlaybackSource):
        """
        Set the playback source.
        0 = U-disk, 1 = SD card, 2 = AUX, 3 = SLEEP, 4 = FLASH
        """
        if source < 0 or source > 4:
            raise ValueError("Playback source must be between 0 and 4")
        # According to the datasheet, this command takes 200ms
        self._exec_command(DFPLAYER_CMD_SET_SOURCE, 0x00, source, 200)

    # def set_playback_mode(self, mode: PlaybackMode):
    #     """
    #     Set the playback mode (0 - 3). 
    #     0 = repeat, 1 = folder repeat, 2 = single repeat, 3 = random.
    #     """
    #     if mode < 0 or mode > 1:
    #         raise ValueError("Playback mode must be 0 or 1")
    #     self._send_command(DFPLAYER_CMD_SET_PLAYBACK_MODE, 0x00, mode)

    def _handle_error_response(self, response_data):
        if response_data == DFPLAYER_ERROR_BUSY:
            raise RuntimeError("DFPlayer is busy")
        if response_data == DFPLAYER_ERROR_FRAME:
            raise RuntimeError("DFPlayer received incomplete frame")
        if response_data == DFPLAYER_ERROR_FCS:
            raise RuntimeError("DFPlayer received corrupted frame (FCS mismatch)")
        if response_data == DFPLAYER_ERROR_NO_SUCH_FILE:
            raise RuntimeError("No such file or folder")
        return super()._handle_error_response(response_data)