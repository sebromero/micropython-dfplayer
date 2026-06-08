import random
from machine import UART, Pin
from time import sleep_ms, ticks_ms, ticks_add, ticks_diff
from dfplayer import DFPlayer

class RandomFolderPlayer:
    def __init__(self, player: DFPlayer, delay_ms: int = None):
        self.player = player
        self.current_folder = None
        self.playlist = []
        self._next_track_time = 0
        self.delay_ms = delay_ms
        
        # Register the callback to know when a track finishes
        self.player.on_track_finished(self._on_track_finished)

    def _shuffle(self):
        # A basic Fisher-Yates shuffle is used
        for i in range(len(self.playlist) - 1, 0, -1):
            j = random.randrange(0, i + 1)
            self.playlist[i], self.playlist[j] = self.playlist[j], self.playlist[i]

    def play_folder(self, folder_id: int):
        self.current_folder = folder_id
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
        
        # Use play_track_large to play the given track from the folder
        try:
            print(f"Playing track {track} in folder {self.current_folder}...")
            self.player.play_track_large(self.current_folder, track)
        except Exception as e:
            print(f"Error playing track {track} from folder {self.current_folder}: {e}")

    def _on_track_finished(self, track_id):
        # A track is done, play the next one
        print(f"Track {track_id} finished.")
        if self.done:
            print("All tracks in the folder have been played.")
            return
        
        if self.delay_ms:
            # Schedule next track
            self._next_track_time = ticks_add(ticks_ms(), self.delay_ms)
        else:
            self.next_track()

    def update(self):
        # Check if it's time to play the next track
        if self._next_track_time > 0 and ticks_diff(ticks_ms(), self._next_track_time) >= 0:
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

    random_player = RandomFolderPlayer(player, delay_ms=2000)
    
    # Start playback for folder number 1
    random_player.play_folder(6) # Change to the desired folder number

    try:
        # Main loop to allow for asynchronous frame processing and calling callbacks
        while True:
            # player.update()
            # random_player.update()
            sleep_ms(50)

            if random_player.done and not player.playing:
                print("Finished playing all tracks in the folder.")
                break
            # sleep_ms(5000)
            # random_player.next_track() # Manually trigger next track for testing without relying on notifications
    except KeyboardInterrupt:
        print("Stopping playback")
        player.stop()

if __name__ == "__main__":
    main()
