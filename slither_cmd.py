from cmd import Cmd
from slither_fat12 import FAT12

class Slither_CMD(Cmd):
    intro = "Slither CMD. Type help or ? for a list of commands.\n"
    prompt = "()> "

    def __init__(self):
        Cmd.__init__(self)
        self.disk = FAT12()

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

    def do_dir(self, arg):
        "dir <>"

        if len(arg):
            self.arg_count()
            return False

        if self.disk.isMounted():
            for i in self.disk.getDir():
                print(i)
        else:
            print("No disk mounted!")

    def do_exit(self, arg):
        "Exits out of the prompt."
        return True

if __name__ == "__main__":
    Slither_CMD().cmdloop()
