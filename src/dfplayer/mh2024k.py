from micropython import const
from .dfplayer import DFPlayer

DFPLAYER_CMD_FILES_IN_FOLDER = const(0x4e)  # Get the number of files in the current folder.
DFPLAYER_CMD_FOLDERS = const(0x4f)  # Get the number of folders.

# DFPLAYER_CMD_FILE_LARGE = const(0x14)  # Play the given file (1-4095) in the given folder (1-15).
# DFPLAYER_CMD_ABORT_ADVERT = const(0x15)  # Abort advert playback and resume current playback.
# DFPLAYER_CMD_RANDOM = const(0x18)  # Start playing all files in random order.
# DFPLAYER_CMD_REPEAT = const(0x19)  # 0 = repeat currently played file, 1 = stop repeating
# DFPLAYER_CMD_ADVERT_FOLDER = const(0x25) # Set the advert folder 1-9

class PlaybackSource:
    USB = 1
    SD_CARD = 2
    FLASH = 4

class MH2024KPlayer(DFPlayer):

    # OVERRIDES

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

    @property
    def software_version(self) -> int | None:
        raise NotImplementedError("MH2024KPlayer should support software version but it's broken.")

    # Additional commands

    # TODO: Doesn't seem to work on MH2024K
    # Returns no data
    @property
    def folder_count(self) -> int | None:
        """Return the number of folders on the current storage device."""
        response = self._exec_command(DFPLAYER_CMD_FOLDERS, is_query=True)
        return response.data if response else None
    
    # TODO: Doesn't seem to work on MH2024K
    # Returns always 0
    @property
    def file_count_in_current_folder(self) -> int | None:
        """Return the number of files in the current folder."""
        response = self._exec_command(DFPLAYER_CMD_FILES_IN_FOLDER, is_query=True)
        return response.data if response else None