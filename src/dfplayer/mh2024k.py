from micropython import const
from .dfplayer import DFPlayer


DFPLAYER_CMD_SINGLE_TRACK_LOOP = const(0x08)  # Loops single track (0-65535)
DFPLAYER_CMD_FILES_IN_FOLDER = const(0x4e)  # Get the number of files in the current folder.
DFPLAYER_CMD_FOLDERS = const(0x4f)  # Get the number of folders.

# DFPLAYER_CMD_FILE_LARGE = const(0x14)  # Play the given file (1-4095) in the given folder (1-15).
# DFPLAYER_CMD_ABORT_ADVERT = const(0x15)  # Abort advert playback and resume current playback.
# DFPLAYER_CMD_REPEAT_FOLDER = const(0x17)  # Start repeat-playing the given folder (1-99)
# DFPLAYER_CMD_RANDOM = const(0x18)  # Start playing all files in random order.
# DFPLAYER_CMD_REPEAT = const(0x19)  # 0 = repeat currently played file, 1 = stop repeating
# DFPLAYER_CMD_ADVERT_FOLDER = const(0x25) # Set the advert folder 1-9

# Error codes sent as parameter of error messages
# DFPLAYER_ERROR_BUSY = const(0x01)  # Module is busy.
# DFPLAYER_ERROR_FRAME = const(0x03)  # Received incomplete frame.
# DFPLAYER_ERROR_FCS = const(0x04)  # Frame check sequence of last frame didn't match.

class PlaybackSource:
    USB = 1
    SD_CARD = 2
    FLASH = 4

class MH2024KPlayer(DFPlayer):

    # OVERRIDES

    def play_track_by_number(self, track_number):
        """
        Play the given track number from the flattened file list.
        The order of tracks is determined by the underlying file table.
        Hence the order of copying files to the storage influences the order.
        Folders are ignored.
        """
        if track_number < 0 or track_number > 65535:
            raise ValueError("Track number must be between 0 and 65535")            
        super().play_track_by_number(track_number)

    def repeat_all(self, repeat):
        # TODO: Further investigate this
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

    def loop_track(self, track_id):
        """
        Loop the given track ID (0-65535) indefinitely. Starts playback.
        The index is the file number from the flattened file list sorted alphabetically.
        """
        self._exec_command(DFPLAYER_CMD_SINGLE_TRACK_LOOP, track_id >> 8, track_id & 0xFF, check_error=True)
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