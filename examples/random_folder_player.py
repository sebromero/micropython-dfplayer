from machine import UART, Pin
from time import sleep_ms
from dfplayer import DFPlayer, RandomFolderPlayer

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

            if random_player.playlist_empty and not player.playing:
                print("Finished playing all tracks in the folder.")
                break
    except KeyboardInterrupt:
        print("Stopping playback")
        player.stop()

if __name__ == "__main__":
    main()
