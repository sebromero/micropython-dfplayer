# 1. Shared Commands (Equal Function)

These commands share the same Hex code and perform the same or nearly identical functions in both modules.

| Command (Hex) | Function            | Parameters / Notes                                     |
| :------------ | :------------------ | :----------------------------------------------------- |
| 0x01          | Next Song           |                                                        |
| 0x02          | Previous Song       |                                                        |
| 0x03          | Specify Track Index | Play specific track number (0-2999/65535)              |
| 0x04          | Volume Up           |                                                        |
| 0x05          | Volume Down         |                                                        |
| 0x06          | Specify Volume      | Set volume level (0-30)                                |
| 0x07          | Specify EQ          | 0-5 (Normal, Pop, Rock, Jazz, Classic, Bass)           |
| 0x0A          | Standby / Sleep     | Enter low power mode                                   |
| 0x0C          | Reset               | Reset the module                                       |
| 0x0D          | Play                | Resume playback                                        |
| 0x0E          | Pause               | Pause playback                                         |
| 0x0F          | Play File in Folder | Play specific file in specific folder                  |
| 0x11          | Loop/Repeat Play    | 1: Start Loop, 0: Stop Loop                            |
| 0x42          | Query Status        | Returns current status (Play/Pause/Stop)               |
| 0x43          | Query Volume        | Returns current volume                                 |
| 0x44          | Query EQ            | Returns current EQ                                     |
| 0x45          | Query Mode          | Returns playback mode                                  |
| 0x46          | Query Version       | Returns software version                               |
| 0x49          | Query Flash Files   | Returns total file count on Flash                      |
| 0x4D          | Query Flash Track   | Returns current track index on Flash                   |

# 2. GD3200B / MH2024K Specific or Conflicting Commands

These commands appear in Document 1 but are either unique to this chip or have a different function/definition than the DFPlayer Mini.

| Command (Hex) | Function (GD3200B)              | Reason for Separation                                                                            |
| :------------ | :------------------------------ | :----------------------------------------------------------------------------------------------- |
| 0x08          | Single Cycle Play (Track Index) | Conflict: Takes a track index to loop. DFPlayer uses 0x08 to set a playback mode (Repeat/Random). |
| 0x09          | Specify Device (Bitmask)        | Conflict: Uses bitmask (1=U-Disk, 2=TF, 4=Flash). DFPlayer uses indexes (0=U-Disk, 1=TF, etc.).  |
| 0x0B          | NC (Reserved)                   | Conflict: Listed as "No Connection". DFPlayer uses 0x0B for "Normal Working".                    |
| 0x10          | NC (Reserved)                   | Conflict: Listed as "No Connection". DFPlayer uses 0x10 for "Volume Adjust Set".                 |
| 0x12          | Play "MP3" Folder               | Unique: Plays files from "MP3" folder.                                                           |
| 0x13          | Advert Interjection             | Unique: Plays from "ADVERT" folder, resumes background.                                          |
| 0x14          | Play Large Folder               | Unique: Supports folders 01-15, files up to 4095.                                                |
| 0x15          | Stop Interjection               | Unique: Stops the inserted advertisement.                                                        |
| 0x16          | Stop                            | Unique: Stops playback completely.                                                               |
| 0x17          | Loop Folder                     | Unique: Loops all files in a specific folder.                                                    |
| 0x18          | Random Play                     | Unique: Random playback command.                                                                 |
| 0x19          | Set Loop Mode                   | Unique: Toggle single loop (0/1).                                                                |
| 0x1A          | Set Mute                        | Unique: Mute/Unmute.                                                                             |
| 0x22          | Play Index & Vol                | Unique: (GD3300B only) Set volume and track in one command.                                      |
| 0x25          | Multi-Folder Advert             | Unique: Interject from folders ADVERT1-9.                                                        |
| 0x47          | Query U-Disk Files              | Conflict: GD3200B queries U-Disk here. DFPlayer queries TF Card.                                 |
| 0x48          | Query TF Files                  | Conflict: GD3200B queries TF Card here. DFPlayer queries U-Disk.                                 |
| 0x4A          | NC (Reserved)                   | Conflict: GD3200B lists as NC. DFPlayer uses for "Keep On".                                      |
| 0x4B          | Query U-Disk Track              | Conflict: GD3200B queries U-Disk here. DFPlayer queries TF Card.                                 |
| 0x4C          | Query TF Track                  | Conflict: GD3200B queries TF Card here. DFPlayer queries U-Disk.                                 |
| 0x4E          | Query Folder Files              | Unique: Get file count in current folder.                                                        |
| 0x4F          | Query Folder Count              | Unique: Get total folder count.                                                                  |

# 3. DFPlayer Mini Specific or Conflicting Commands

These commands appear in Document 2 but are either unique to the DFPlayer Mini or have a different function/definition than the GD3200B.

| Command (Hex) | Function (DFPlayer)    | Reason for Separation                                                                                      |
| :------------ | :--------------------- | :--------------------------------------------------------------------------------------------------------- |
| 0x08          | Specify Playback Mode  | Conflict: Sets mode (0=Repeat, 1=Folder, 2=Single, 3=Random). GD3200B uses 0x08 to loop a specific track.  |
| 0x09          | Specify Source (Index) | Conflict: Uses Index (0=U, 1=TF, 2=AUX, 3=SLEEP, 4=FLASH). GD3200B uses bitmask.                           |
| 0x0B          | Normal Working         | Conflict: Wake from standby. GD3200B lists as Reserved.                                                    |
| 0x10          | Volume Adjust Set      | Conflict: Adjust volume gain. GD3200B lists as Reserved.                                                   |
| 0x47          | Query TF Files         | Conflict: DFPlayer queries TF Card here. GD3200B queries U-Disk.                                           |
| 0x48          | Query U-Disk Files     | Conflict: DFPlayer queries U-Disk here. GD3200B queries TF Card.                                           |
| 0x4A          | Keep On                | Conflict: DFPlayer command. GD3200B lists as Reserved.                                                     |
| 0x4B          | Query TF Track         | Conflict: DFPlayer queries TF Card here. GD3200B queries U-Disk.                                           |
| 0x4C          | Query U-Disk Track     | Conflict: DFPlayer queries U-Disk here. GD3200B queries TF Card.                                           |