# Control Commands

| Command (Hex) | Function                | Parameters / Description                                                     |
| :------------ | :---------------------- | :--------------------------------------------------------------------------- |
| 0x01          | Next                    | Play next song                                                               |
| 0x02          | Previous                | Play previous song                                                           |
| 0x03          | Specify Tracking        | Parameter: Track number (0–2999)                                             |
| 0x04          | Increase Volume         | Increment volume                                                             |
| 0x05          | Decrease Volume         | Decrement volume                                                             |
| 0x06          | Specify Volume          | Parameter: Volume level (0–30)                                               |
| 0x07          | Specify EQ              | Parameter: 0=Normal, 1=Pop, 2=Rock, 3=Jazz, 4=Classic, 5=Bass                |
| 0x08          | Specify Playback Mode   | Parameter: 0=Repeat, 1=Folder Repeat, 2=Single Repeat, 3=Random              |
| 0x09          | Specify Playback Source | Parameter: 0=U-Disk, 1=TF, 2=AUX, 3=SLEEP, 4=FLASH                           |
| 0x0A          | Enter Standby           | Enter low power loss mode                                                    |
| 0x0B          | Normal Working          | Return to normal working state (wake)                                        |
| 0x0C          | Reset Module            | Reset the module                                                             |
| 0x0D          | Playback                | Resume playback                                                              |
| 0x0E          | Pause                   | Pause playback                                                               |
| 0x0F          | Specify Folder          | Parameter: Folder ID (Table says 1-10; text later clarifies 01-99 supported) |
| 0x10          | Volume Adjust Set       | High Byte (DH)=1: Open volume adjust; Low Byte (DL): Set volume gain 0~31    |
| 0x11          | Repeat Play             | Parameter: 1=Start repeat play, 0=Stop play                                  |

# System Query Commands
| Command (Hex) | Function            | Parameters / Description                 |
| :------------ | :------------------ | :--------------------------------------- |
| 0x42          | Query Status        | Returns current status                   |
| 0x43          | Query Volume        | Returns current volume                   |
| 0x44          | Query EQ            | Returns current EQ setting               |
| 0x45          | Query Playback Mode | Returns current playback mode            |
| 0x46          | Query Version       | Returns current software version         |
| 0x47          | Query TF Card Files | Returns total number of files on TF card |
| 0x48          | Query U-Disk Files  | Returns total number of files on U-Disk  |
| 0x49          | Query Flash Files   | Returns total number of files on Flash   |
| 0x4B          | Query TF Track      | Returns current track number on TF card  |
| 0x4C          | Query U-Disk Track  | Returns current track number on U-Disk   |
| 0x4D          | Query Flash Track   | Returns current track number on Flash    | 

# System Responses (Returned Data)
| Command (Hex) | Function                  | Parameters / Description                                                       |
| :------------ | :------------------------ | :----------------------------------------------------------------------------- |
| 0x3A          | Device Inserted           | 01: U-Disk, 02: TF Card                                                        |
| 0x3B          | Device Removed            | 01: U-Disk, 02: TF Card                                                        |
| 0x3C          | U-Disk Track Finished     | Returns track number that just finished                                        |
| 0x3D          | TF Card Track Finished    | Returns track number that just finished                                        |
| 0x3E          | Flash Track Finished      | Returns track number that just finished                                        |
| 0x3F          | Initialization Parameters | Sent on power-up. Bitmask of online devices: 01=U-Disk, 02=TF, 04=PC, 08=Flash |
| 0x40          | Error / Busy              | 00: Busy, 01: Frame data incomplete, 02: Verification error                    |
| 0x41          | Reply                     | General acknowledgment                                                         | 