from tkinter import *
from tkinter import filedialog, messagebox, ttk

from slither_cmd import * # The gui runs off of the command prompt.

def selectItem(event):
    curItem = tree.focus()
    if curItem:
        #editmenu.entryconfigure("Copy", state=NORMAL)
        #editmenu.entryconfigure("Rename", state=NORMAL)
        editmenu.entryconfigure("Delete", state=NORMAL)
        #editmenu.entryconfigure("Pull File", state=NORMAL)

def deselectItem():
        editmenu.entryconfigure("Copy", state=DISABLED)
        editmenu.entryconfigure("Rename", state=DISABLED)
        editmenu.entryconfigure("Delete", state=DISABLED)
        editmenu.entryconfigure("Pull File", state=DISABLED)

def deleteFile():
    curItem = tree.item(tree.focus())
    print(curItem["text"])
    if messagebox.askquestion("Delete", "Are you sure you want to delete \'%s\'?" % curItem["text"], icon="warning") == "yes":
        slither_cmd.do_del((curItem["text"],))
        tree.delete(tree.selection()[0])
        deselectItem()

def mountDisk():
    filename = filedialog.askopenfilename(initialdir = ".",title = "Select file",filetypes = (("Virtual Floppy Disk", ("*.dmg", "*.flp", "*.vfd")), ("all files","*.*")))
    slither_cmd.do_mount((filename,))

    if slither_cmd.disk.isMounted():
        filemenu.entryconfigure("Mount", state=DISABLED)
        filemenu.entryconfigure("Unmount", state=NORMAL)
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

# Create the menu bar.
menubar = Menu(root)

# Create the file menu.
filemenu = Menu(menubar, tearoff=0)
filemenu.add_command(label="New", state=DISABLED)
filemenu.add_command(label="Mount", command=mountDisk)
filemenu.add_command(label="Unmount", command=unmountDisk, state=DISABLED)

filemenu.add_separator()

filemenu.add_command(label="Exit", command=root.quit)

menubar.add_cascade(label="File", menu=filemenu)

# Create the disk menu.
diskmenu = Menu(menubar, tearoff=0)

diskmenu.add_command(label="Info", state=DISABLED)
diskmenu.add_command(label="Space", state=DISABLED)

menubar.add_cascade(label="Disk", menu=diskmenu)

# Create the edit menu.
editmenu = Menu(menubar, tearoff=0)
editmenu.add_command(label="New File", state=DISABLED)
editmenu.add_command(label="New Directory", state=DISABLED)

editmenu.add_separator()

editmenu.add_command(label="Push File", state=DISABLED)
editmenu.add_command(label="Pull File", state=DISABLED)

editmenu.add_separator()

editmenu.add_command(label="Copy", state=DISABLED)
editmenu.add_command(label="Rename", state=DISABLED)
editmenu.add_command(label="Delete", command=deleteFile, state=DISABLED)

menubar.add_cascade(label="Edit", menu=editmenu)

# Create the help menu.
helpmenu = Menu(menubar, tearoff=0)

helpmenu.add_command(label="About", state=DISABLED)

menubar.add_cascade(label="Help", menu=helpmenu)

# Create the tree view.
tree = ttk.Treeview(root, columns=("size", "time", "date"))
tree.heading("#0", text="File")
tree.heading("size", text="Size")
tree.heading("time", text="Modified Time")
tree.heading("date", text="Modified Date")

tree.bind('<ButtonRelease-1>', selectItem)

# Run the gui.
tree.pack()

root.config(menu=menubar)
root.mainloop()
