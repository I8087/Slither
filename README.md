# Slither
Slither is a simple virtual floppy disk explorer that makes manipulating a virtual floppy diske easy. An editing prompt is provided in `slither_cmd.py`. **THIS PROGRAM IS VERY NEW AND UNSTABLE. ALWAYS BACK UP YOUR VIRTUAL DISK BEFORE USING THIS PROGRAM!**

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
* `mount` - Mounts a virtual floppy disk in the current path directory.
* `unmount` - Unmounts a disk, if a disk is mounted.
* `dir` - Displays the contents of the home directory.
* `add` - Loads a file into the virtual floppy disk.
* `del` - Deletes a file on the virtual floppy disk.
* `ren` - Renames a file on the virtual floppy disk.
* `get` - Gets a file off of the virtual floppy disk.
* `help` - Displays help and command information.
* `exit` - Unmounts the disk if mounted and then exits.
