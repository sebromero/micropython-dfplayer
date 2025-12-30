from micropython import const
# from .dfplayer import DFPlayer, DFPLAYER_CMD_PLAY_TRACK, DFPLAYER_CMD_SET_SOURCE
from dfplayer import DFPlayer, DFPLAYER_CMD_SET_SOURCE

# TODO Depends on device. test
DFPLAYER_SINGLE_TRACK_LOOP = const(0x08)  # Loops single track (0-65535)
DFPLAYER_CMD_FILE_LARGE = const(0x14)  # Play the given file (1-4095) in the given folder (1-15).
DFPLAYER_CMD_ABORT_ADVERT = const(0x15)  # Abort advert playback and resume current playback.
DFPLAYER_CMD_REPEAT_FOLDER = const(0x17)  # Start repeat-playing the given folder (1-99)
DFPLAYER_CMD_RANDOM = const(0x18)  # Start playing all files in random order.
DFPLAYER_CMD_REPEAT = const(0x19)  # 0 = repeat currently played file, 1 = stop repeating
DFPLAYER_CMD_ADVERT_FOLDER = const(0x25) # Set the advert folder 1-9

# Notification codes sent by the DFPlayer Mini
DFPLAYER_NOTIFY_INSERT = const(0x3a)  # A USB storage device or an SD card was inserted.
DFPLAYER_NOTIFY_EJECT = const(0x3b)  # A USB storage device or an SD card was ejected.
DFPLAYER_NOTIFY_DONE_USB = const(0x3c)  # Completed playing the indicated track from USB storage.
DFPLAYER_NOTIFY_DONE_SDCARD = const(0x3d)  # Completed playing the indicated track from SD card.
DFPLAYER_NOTIFY_DONE_FLASH = const(0x3e)  # Completed playing the indicated track from flash.

DFPLAYER_CMD_FILES_USB = const(0x47)  # Get the total number of files on USB storage.
DFPLAYER_CMD_FILES_SDCARD = const(0x48)  # Get the total number of files on the SD card.
DFPLAYER_CMD_FILENO_USB = const(0x4b)  # Get the currently select file number on the USB storage.
DFPLAYER_CMD_FILENO_SDCARD = const(0x4c)  # Get the currently select file number on the SD-Card.    
DFPLAYER_CMD_FILES_IN_FOLDER = const(0x4e)  # Get the number of files in the current folder.
DFPLAYER_CMD_FOLDERS = const(0x4f)  # Get the number of folders.
DFPLAYER_MAX_MP3_FILE = const(65536)  # Highest supported file number in the "MP3" folder.

# Device identifiers in insert/eject notifications
# TODO: Test as these are unverified
DFPLAYER_DEVICE_USB = const(0x01)  # A USB storage device was inserted/ejected.
DFPLAYER_DEVICE_SDCARD = const(0x02)  # An SD card was inserted/ejected.

class PlaybackSource:
    USB = 1
    SD_CARD = 2
    FLASH = 4

class GD3200Player(DFPlayer):

    def play_track_by_number(self, track_number):
        """Play the given track number from the current folder"""
        if track_number < 0 or track_number > 65535:
            raise ValueError("Track number must be between 0 and 65535")            
        super().play_track_by_number(track_number)

    # def set_playback_source(self, source : PlaybackSource):
    #     """
    #     Set the playback source.
    #     1: USB, 2: TF Card, 4: Flash
    #     """
    #     if source < 1 or source > 4:
    #         raise ValueError("Playback source must be between 1 and 4")
    #     # According to the datasheet, this command takes 200ms
    #     self._exec_command(DFPLAYER_CMD_SET_SOURCE, 0x00, source, 200)

    # def loop_track(self, track_id):
    #     self.cmd(0x08, track_id)


if __name__ == "__main__":
    from machine import UART, Pin
    uart1 = UART(0, tx=Pin("TX"), rx=Pin("RX"))
    player1 = GD3200Player(uart1)