import random
from machine import UART, Pin, Timer
from time import sleep_ms, ticks_ms, ticks_add, ticks_diff
from micropython import schedule
from dfplayer import DFPlayer

class RandomFolderPlayer:
    def __init__(self, player: DFPlayer, delay_ms: int = None, timer_id: int = 1):
        self.player = player
        self.current_folder = None
        self.large_folder = False
        self.playlist = []
        self._delay_ms = delay_ms
        self._timer_id = timer_id
        
        if self._timer_id is not None and delay_ms is not None:
            self._timer = Timer(self._timer_id) # Using a supported hardware Timer on this board
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
    def done(self):
        return len(self.playlist) == 0

    def next_track(self):
        if self.done:
            print("No more tracks to play in the current folder.")
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
        # A track is done, play the next one
        print(f"Track with ID {track_id} finished.")
        if self.done:
            print("All tracks in the folder have been played.")
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
        # Check if it's time to play the next track (when not using hardware timer)
        if self._timer_id is None and self._next_track_time > 0 and ticks_diff(ticks_ms(), self._next_track_time) >= 0:
            self._next_track_time = 0
            self.next_track()

player = None
random_player = None

def main():
    global player, random_player
    uart = UART(0, tx=Pin("TX"), rx=Pin("RX")) # Adjust pins as needed
    busy_pin = Pin("D5") # Optional busy pin
    
    player = DFPlayer(uart=uart, busy_pin=busy_pin, use_irq=True)
    
    # Set volume
    player.volume = 50

    # Pass timer_id=1 to use a hardware timer, or None to fall back to update() polling
    random_player = RandomFolderPlayer(player, delay_ms=2000, timer_id=1)
    
    # Start playback for folder number 6 
    # Use large_folder=True if using file numbers > 255 OR matching 4-digit formatting (06/0001.mp3)
    random_player.play_folder(6, large_folder=True) 

    try:
        # Main loop to allow for asynchronous frame processing and calling callbacks
        while True:
            # player.update() # Uncomment if not using IRQ for frame processing
            # random_player.update() # Uncomment if not using hardware timer for delays
            sleep_ms(50)

            if random_player.done and not player.playing:
                print("Finished playing all tracks in the folder.")
                break
    except KeyboardInterrupt:
        print("Stopping playback")
        player.stop()

if __name__ == "__main__":
    main()
