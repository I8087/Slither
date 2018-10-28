import sys
from cmd import Cmd
from slither_fat12 import *

class Slither_CMD(Cmd):
    intro = "Slither CMD. Type help or ? for a list of commands.\n"
    prompt = "()> "

    def __init__(self, argv):
        Cmd.__init__(self)
        self.disk = FAT12()
        self.cmdqueue.extend(argv) # Execute argv

    # ----- Cmd Methods -----

    # Change the unknown command method.
    def default(self, line):
        print("Unknown command! ", end="")
        self._helpmsg(line)

    def _helpmsg(self, line=""):
        print("Type help or ? for a list of commands.")

    def arg_count(self):
        print("Not the right number of args passed.")
        self._helpmsg()

    # Return a tuple instead of a string.
    def parseline(self, line):
        cmd, arg, line = Cmd.parseline(self, line)

        if cmd:
            cmd = cmd.lower()

        if cmd not in ("help", "?"):
            if arg:
                arg = tuple(arg.split())
            else:
                arg = tuple()

        return cmd, arg, line

    #def do_help(self, arg):
    #    return Cmd.do_help(self, str(arg))

    # ----- Slither Commands -----
    def do_mount(self, arg):
        "mount <path>"

        if len(arg) != 1:
            self.arg_count()
            return False

        if self.disk.isMounted():
            print("Already mounted!")
        else:
            if self.disk.mount(arg[0]):
                print("Sucessfully mounted the disk.")
                self.prompt = "(%s)> " % arg[0].split("\\")[-1]
            else:
                print("Failed to mount the disk!")

    def do_unmount(self, arg):
        "unmount <>"

        if len(arg):
            self.arg_count()
            return False

        if self.disk.isMounted():
            if self.disk.unmount():
                print("Sucessfully unmounted the disk.")
                self.prompt = "()> "
            else:
                print("Failed to unmount the disk.")
        else:
            print("No disk mounted!")

    def do_boot(self, arg):
        "boot <bootloader>"

        if len(arg) != 1:
            self.arg_count()
            return False

        try:
            self.disk.addBootloader(arg[0])
            print("Succesfully added the bootloader!")

        except SlitherIOError as e:
            print(e.msg)

    def do_dir(self, arg):
        "dir <>"

        if len(arg):
            self.arg_count()
            return False

        try:
            print("Directory of drive:\n")
            for i in self.disk.getDir():
                print("{:<14}   {:>5} BYTES   {}   {}".format(i[0], i[1], i[2], i[3]))

        except SlitherIOError as e:
            print(e.msg)

    def do_add(self, arg):
        "add <file>"

        if len(arg) != 1:
            self.arg_count()
            return False

        try:
            # Read the contents of the file.
            f = open(arg[0], "rb")
            cnt = f.read()
            f.close()

            self.disk.addFile(arg[0], cnt)

            print("Successfully added the file!")

        except IOError:
            print("Unable to read the file!")

        except SlitherIOError as e:
            print(e.msg)

    def do_del(self, arg):
        "del <file>"

        if len(arg) != 1:
            self.arg_count()
            return False

        try:
            self.disk.deleteFile(arg[0])
            print("Successfully deleted the file!")

        except SlitherIOError as e:
            print(e.msg)


    def do_ren(self, arg):
        "ren <oldfile> <newfile>"

        if len(arg) != 2:
            self.arg_count()
            return False

        try:
            self.disk.renameFile(arg[0], arg[1])
            print("Succesfully renamed the file!")

        except SlitherIOError as e:
            print(e.msg)

    def do_get(self, arg):
        "get <file> optional <newfile>"

        if len(arg) not in (1, 2):
            self.arg_count()
            return False

        try:
            c = self.disk.getFile(arg[0])
            print(len(c))

            if len(arg) == 2:
                f = open(arg[1], "wb")
            else:
                f = open(arg[0], "wb")

            f.write(c)
            f.close()
            print("Successfully got the file!")

        except IOError:
            print("Unable to create file!")

        except SlitherIOError as e:
            print(e.msg)

    def do_exit(self, arg):
        "Exits out of the prompt."

        # Make sure to properly unmount.
        if self.disk.isMounted():
            self.do_unmount(arg)

        print("Goodbye!")
        return True

if __name__ == "__main__":

    # Create our own argv with
    # semicolons as seperators.
    argv = ""

    for i in sys.argv[1:]:
        argv += "%s " % i

    argv = argv.strip().split(";")

    Slither_CMD(argv).cmdloop()
