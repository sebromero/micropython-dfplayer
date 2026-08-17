import random
from machine import Timer
from time import ticks_ms, ticks_add, ticks_diff
from micropython import schedule
from .dfplayer import DFPlayer

class RandomFolderPlayer:
    """
    A helper class to play all tracks in a given folder in random order.
    It listens for track completion events from the DFPlayer and automatically advances to the next track 
    in the shuffled playlist until all tracks have been played.
    """
    def __init__(self, player: DFPlayer, delay_ms: int = None, timer_id: int = 1):
        self.player = player
        self.current_folder = None
        self.large_folder = False
        self.playlist = None
        self._delay_ms = delay_ms
        self._timer_id = timer_id
        
        if self._timer_id is not None and delay_ms is not None:
            self._timer = Timer(self._timer_id)
        else:
            self._next_track_time = 0
        
        # Register the callback to know when a track finishes
        self.player.on_track_finished(self._on_track_finished)

    def _shuffle(self):
        # A basic Fisher-Yates shuffle is used
        for i in range(len(self.playlist) - 1, 0, -1):
            j = random.randrange(0, i + 1)
            self.playlist[i], self.playlist[j] = self.playlist[j], self.playlist[i]

    def play_folder(self, folder_id: int, large_folder: bool = False):
        """
        Start playing all tracks in the given folder in random order.

        Parameters:
            folder_id: The ID of the folder to play (1-15)
            large_folder: Set to True if using file numbers > 255 or matching 4-digit formatting (06/0001.mp3)
        """
        self.current_folder = folder_id
        self.large_folder = large_folder
        # Check how many tracks are in this folder
        count = self.player.file_count_in_folder(self.current_folder)
        if not count:
            print(f"No files found in folder {self.current_folder}")
            return
            
        print(f"Found {count} files in folder {self.current_folder}")
        
        # Create a list of tracks and calculate a random sequence
        self.playlist = list(range(1, count + 1))
        self._shuffle()

        print(f"Shuffled playlist for folder {self.current_folder}: {self.playlist}")
        
        # Start playing the first track in the sequence
        self.next_track()

    @property
    def playlist_empty(self):
        """
        Returns True if there are no tracks left to play in the current playlist, False otherwise.
        """
        return self.playlist is None or len(self.playlist) == 0

    def reset(self):
        """
        Reset the playlist and current folder.
        Use this to stop the player from accidentally
        advancing to the next track if a "done" notification is received 
        that stems from an interaction with the player outside of this class 
        (e.g. using the DFPlayer's play/stop methods directly).
        """
        self.playlist = None
        self.current_folder = None

    def next_track(self):
        """
        Play the next track in the shuffled playlist. If the playlist is empty, do nothing.
        """
        if self.playlist_empty:
            return
        
        if self.current_folder is None:
            print("No folder selected.")
            return
        
        # Pop the next track number from the list
        track = self.playlist.pop(0)
        
        # Use play_track or play_track_large to play the given track from the folder
        try:
            print(f"Playing track {track} in folder {self.current_folder}...")
            if self.large_folder:
                self.player.play_track_large(self.current_folder, track)
            else:
                self.player.play_track(self.current_folder, track)
        except Exception as e:
            print(f"Error playing track {track} from folder {self.current_folder}: {e}")

    def _on_track_finished(self, track_id):
        if self.playlist is None:
            # No playlist selected. Ignoring 'track finished' event"
            return

        # A track is done, play the next one
        print(f"Track with ID {track_id} finished.")
        
        if self.playlist is not None and self.playlist_empty:
            print("All tracks in the folder have been played.")
            self.playlist = None
            return
        
        if self._delay_ms:
            if self._timer_id is not None:
                # The timer callback runs in an IRQ context, where waiting for UART ACKs is unsafe.
                # We use micropython.schedule to execute the next_track method safely in the main loop.
                self._timer.init(period=self._delay_ms, mode=Timer.ONE_SHOT, callback=lambda t: schedule(self._safe_next_track, None))
            else:
                self._next_track_time = ticks_add(ticks_ms(), self._delay_ms)
        else:
            self.next_track()

    def _safe_next_track(self, _):
        # micropython.schedule requires a callback that accepts exactly one argument.
        # This wrapper absorbs that argument (None) and safely calls next_track().
        self.next_track()

    def update(self):
        """
        If not using a hardware timer for delays, this method should be called 
        regularly (e.g. in the main loop)
        """
        # Check if it's time to play the next track (when not using hardware timer)
        if self._timer_id is None and self._next_track_time > 0 and ticks_diff(ticks_ms(), self._next_track_time) >= 0:
            self._next_track_time = 0
            self.next_track()