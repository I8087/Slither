# Slither
Slither is a simple virtual floppy disk explorer that makes manipulating a virtual floppy disk easier. The editing prompt is provided as `slither_cmd.py` and a user-friendly gui version of the program is `slither_gui.pyw`. **THIS PROGRAM IS SOMEWHAT NEW AND UNSTABLE. ALTHOUGH I'VE MADE A LOT OF PROGRESS ON STABILITY, YOU SHOULD STILL BACK UP YOUR VIRTUAL FLOPPY DISKS BEFORE USING THIS PROGRAM!**

## Getting Started
Here's an example of the prompt.

```
Slither CMD. Type help or ? for a list of commands.

()> mount myfloppy.flp
Sucessfully mounted the disk.
(myfloppy.flp)> dir
Directory of drive:

EDIT.BIN
NOTES.TXT
KERNEL.SYS
(myfloppy.flp)> add CALC.BIN
(myfloppy.flp)> dir
Directory of drive:

CALC.BIN
EDIT.BIN
NOTES.TXT
KERNEL.SYS
(myfloppy.flp)> unmount
Sucessfully unmounted the disk.
()> exit
```

You can pass a list of commands before the script runs by using a semicolon (;) to seperate them. Ex: `py -3 slither_cmd.py mount myfloppy.flp;dir;add CALC.BIN;dir;unmount`

## List of Commands
* `boot` - Loads a bootloader file at the beginning of the first logical sector.
* `mount` - Mounts a virtual floppy disk in the current path directory.
* `unmount` - Unmounts a disk, if a disk is mounted.
* `format` - Wipes and reformats the disk.
* `dir` - Displays the contents of the home directory.
* `del` - Deletes a file on the virtual floppy disk.
* `ren` - Renames a file on the virtual floppy disk.
* `pull` - Gets a file off of the virtual floppy disk.
* `push` - Loads a file into the virtual floppy disk.
* `help` - Displays help and command information.
* `exit` - Unmounts the disk if mounted and then exits.
