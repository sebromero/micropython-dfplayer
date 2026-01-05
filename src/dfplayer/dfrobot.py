from micropython import const
from .dfplayer import DFPlayer

DFPLAYER_CMD_STANDBY_EXIT = const(0x0b)  # Exit low power mode, back to normal mode.
DFPLAYER_CMD_VOLUME_ADJUST_SET = const(0x10) # Set the DAC gain. (0-31)

class PlaybackSource:
    USB = 0
    SD_CARD = 1
    AUX = 2
    SLEEP = 3
    FLASH = 4

class DFRobotPlayer(DFPlayer):

    # OVERRIDES

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

    