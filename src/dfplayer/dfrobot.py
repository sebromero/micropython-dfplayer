from micropython import const
from .dfplayer import DFPlayer

DFPLAYER_CMD_STANDBY_EXIT = const(0x0b)  # Exit low power mode, back to normal mode.
DFPLAYER_CMD_VOLUME_ADJUST_SET = const(0x10) # Set the DAC gain. (0-31)

DFPLAYER_CMD_GET_FILES_SDCARD = const(0x47)  # Get the total number of files on the SD card.
DFPLAYER_CMD_GET_FILES_USB = const(0x48)  # Get the total number of files on USB storage.
DFPLAYER_CMD_FILENO_SDCARD = const(0x4b)  # Get the currently select file number on the SD-Card.
DFPLAYER_CMD_FILENO_USB = const(0x4c)  # Get the currently select file number on the USB storage.

class PlaybackSource:
    USB = 0
    SD_CARD = 1
    AUX = 2
    SLEEP = 3
    FLASH = 4

class DFRobotPlayer(DFPlayer):

    # OVERRIDES

    def play_track_by_number(self, track_number):
        """
        Play the given track number from the flattened file list.
        The order of tracks is determined by the underlying file table.
        Hence the order of copying files to the storage influences the order.
        Folders are NOT ignored. Trying to play a track that represents a folder
        will result in no playback.
        """
        if track_number < 0 or track_number > 2999:
            raise ValueError("Track number must be between 0 and 2999")            
        super().play_track_by_number(track_number)

    # TODO: This needs testing
    def set_playback_source(self, source : int):
        """
        Set the playback source.
        0 = U-disk, 1 = SD card, 2 = AUX, 3 = SLEEP, 4 = FLASH
        """
        if source < 0 or source > 4:
            raise ValueError("Playback source must be between 0 and 4")
        
        super().set_playback_source(source)

    # Additional commands

    # TODO: Doesn't seem to work on DFROBOT|LISP3
    # Device keeps sending error responses after sending this command
    def exit_standby(self):
        """Exit low power mode, back to normal mode."""
        self._exec_command(DFPLAYER_CMD_STANDBY_EXIT)

    # TODO: Doesn't seem to work on DFROBOT|LISP3
    # Device acknowledges the command but gain doesn't change
    def set_dac_gain(self, enabled: bool, gain: int = 31):
        """
        Set the DAC gain (0 - 31). This adjusts the output volume level.
        When 'enabled' is False, the gain setting is ignored and the DAC uses default gain
        """
        if gain < 0 or gain > 31:
            raise ValueError("DAC gain must be between 0 and 31")
        # HD-byte value, 0x01=enable gain, 0x00=disable gain
        # LD-byte value, 0..31=gain
        self._exec_command(DFPLAYER_CMD_VOLUME_ADJUST_SET, 0x01 if enabled else 0x00, gain)

    