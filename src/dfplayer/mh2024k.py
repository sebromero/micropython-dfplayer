from micropython import const
from .dfplayer import DFPlayer

DFPLAYER_CMD_REPEAT = const(0x19)  # 0 = repeat currently played file, 1 = stop repeating

class PlaybackSource:
    USB = 1
    SD_CARD = 2
    FLASH = 4

class MH2024KPlayer(DFPlayer):

    # OVERRIDES
    @property
    def software_version(self) -> int | None:
        raise NotImplementedError("MH2024KPlayer should support software version but it's broken.")
    
    def repeat_all(self, repeat):
        # Device seems to acknowledge the command but doesn't do anything
        raise NotImplementedError("MH2024KPlayer should support repeat all but it's broken.")

    # TODO: This needs testing
    def set_playback_source(self, source : int):
        """
        Set the playback source.
        1: USB, 2: TF Card, 4: Flash
        """
        if source < 1 or source > 4:
            raise ValueError("Playback source must be between 1 and 4")
        
        super().set_playback_source(source)

    # Additional commands

    # Doesn't seem to work
    def loop_current_track(self, enable: bool):
        """
        Start or stop repeat-playing the current track.
        """
        if not self.playing:
            raise RuntimeError("No track is currently playing")
        value = 0x01 if enable else 0x00
        self._exec_command(DFPLAYER_CMD_REPEAT, 0x00, value)
