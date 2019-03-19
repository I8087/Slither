from tkinter import *
from tkinter import filedialog
from tkinter import ttk

from slither_cmd import * # The gui runs off of the command prompt.

def mountDisk():
    filename = filedialog.askopenfilename(initialdir = ".",title = "Select file",filetypes = (("Virtual Floppy Disk", ("*.vfd", "*.flp")),("all files","*.*")))
    slither_cmd.do_mount((filename,))

    if slither_cmd.disk.isMounted():
        filemenu.entryconfigure("Mount", state = DISABLED)
        filemenu.entryconfigure("Unmount", state = NORMAL)
        root.title("Slither - [%s]" % filename)
        for i in slither_cmd.disk.getDir():
            tree.insert("", "end", text=i[0], values=("%s Bytes" % i[1], i[2], i[3]))

def unmountDisk():
        slither_cmd.do_unmount(tuple())
        filemenu.entryconfigure("Unmount", state = DISABLED)
        filemenu.entryconfigure("Mount", state = NORMAL)
        root.title("Slither - []")
        tree.delete(*tree.get_children())

# Let Slither know that the gui is running.
SLITHER_GUI = True

slither_cmd = Slither_CMD("")

# Create the base for our gui.
root = Tk()
root.title("Slither - []")

menubar = Menu(root)
filemenu = Menu(menubar, tearoff=0)
filemenu.add_command(label="New", state=DISABLED)
filemenu.add_command(label="Mount", command=mountDisk)
filemenu.add_command(label="Unmount", command=unmountDisk, state=DISABLED)

filemenu.add_separator()

filemenu.add_command(label="Exit", command=root.quit)

menubar.add_cascade(label="File", menu=filemenu)

# Create the tree view.
tree = ttk.Treeview(root, columns=("size", "time", "date"))
tree.heading("#0", text="File")
tree.heading("size", text="Size")
tree.heading("time", text="Modified Time")
tree.heading("date", text="Modified Date")

# Run the gui.
tree.pack()

root.config(menu=menubar)
root.mainloop()
