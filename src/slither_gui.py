#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
from tkinter import *
from tkinter import filedialog, messagebox, simpledialog, ttk
from PIL import Image, ImageTk

from slither_cmd import * # The gui runs off of the command prompt.
from slither_icons import *

aboutstr = """\
Slither - Virtual Floppy Disk Editor.
Copyright (c) 2018-2020, Nathaniel Yodock
All rights reserved.

Icons generated with Feather. https://feathericons.com/
Copyright (c) 2013-2017, Cole Bemis"""


def onDoubleClick(event):
    curItem = tree.item(tree.focus())

    e = slither_cmd.disk.getDir()
    e_dir = [i for i in e if e[i]["IS_DIRECTORY"]]

    if curItem["text"] in e_dir:
        slither_cmd.do_cd((curItem["text"],))
        refreshTree()

# show the menu bar with a right click.
def showMenu(event):

    r = tree.identify_row(event.y)
    if r:
        tree.focus(r)
        tree.selection_set(r)

    selectItem(event)
    menubar.post(event.x_root, event.y_root)

def selectItem(event):
    curItem = tree.focus()
    if curItem:
        #editmenu.entryconfigure("Copy", state=NORMAL)
        editmenu.entryconfigure("Rename", state=NORMAL)
        editmenu.entryconfigure("Delete", state=NORMAL)
        editmenu.entryconfigure("Pull File", state=NORMAL)

def deselectItem():
    editmenu.entryconfigure("Copy", state=DISABLED)
    editmenu.entryconfigure("Rename", state=DISABLED)
    editmenu.entryconfigure("Delete", state=DISABLED)
    editmenu.entryconfigure("Pull File", state=DISABLED)

def deleteFile():
    curItem = tree.item(tree.focus())
    if messagebox.askquestion("Delete", "Are you sure you want to delete \'%s\'?" % curItem["text"], icon="warning") == "yes":
        slither_cmd.do_del((curItem["text"],))
        refreshTree()

def renameFile():
    curItem = tree.item(tree.focus())
    a = simpledialog.askstring("Rename", "Input the new file name:")
    if a:
        slither_cmd.do_ren((curItem["text"], a))
        refreshTree()

def pullFile():
    curItem = tree.item(tree.focus())
    #filename = filedialog.asksaveasfilename(initialdir = ".", title = "Save File")
    slither_cmd.do_pull((curItem["text"],))

def pushFile():
    filename = filedialog.askopenfilename(initialdir = ".", title = "Select File")
    slither_cmd.do_push((filename,))
    refreshTree()

def mountDisk():
    filename = filedialog.askopenfilename(initialdir = ".", title = "Select Disk",filetypes = (("Virtual Floppy Disk", ("*.dmg", "*.flp", "*.vfd")), ("all files", "*.*")))
    slither_cmd.do_mount((filename,))

    if slither_cmd.disk.isMounted():
        filemenu.entryconfigure("Mount", state=DISABLED)
        filemenu.entryconfigure("Unmount", state=NORMAL)
        editmenu.entryconfigure("Push File", state=NORMAL)
        root.title("Slither - [%s]" % filename)
        refreshTree()

def unmountDisk():
        slither_cmd.do_unmount(tuple())
        filemenu.entryconfigure("Unmount", state = DISABLED)
        filemenu.entryconfigure("Mount", state = NORMAL)
        editmenu.entryconfigure("Push File", state=DISABLED)
        deselectItem()
        root.title("Slither - []")
        tree.delete(*tree.get_children())

def refreshTree():
    tree.delete(*tree.get_children())

    e = slither_cmd.disk.getDir()
    dis_dir = [i for i in e if e[i]["IS_DIRECTORY"]]
    dis_files = [i for i in e if e[i]["IS_FILE"]]

    for i in sorted(dis_dir, key=str.lower):

        tree.insert("",
                    "end",
                    text=i,
                    values=("", e[i]["MODIFIED_TIME_STR"], e[i]["MODIFIED_DATE_STR"]),
                    image=images["Folder"])


    for i in sorted(dis_files, key=str.lower):

        # Get appropriate size.
        b = e[i]["SIZE"]
        pf = "B"
        if b > 1024:
            b = b // 1024
            pf = "KiB"

        tree.insert("",
                    "end",
                    text=i,
                    values=("{} {}".format(b, pf), e[i]["MODIFIED_TIME_STR"], e[i]["MODIFIED_DATE_STR"]),
                    image=images["File"])


def sortSize(reverse):
    l = []

    for i in tree.get_children(""):
        s = tree.set(i, "size").split()
        s[0] = int(s[0])

        if s[1] == "KiB":
            s[0] *= 1024

        l.append((s[0], i))
        
    l.sort(reverse=reverse)

    for index, (val, i) in enumerate(l):
        tree.move(i, "", index)

    # reverse sort next time
    tree.heading("size", text="Size", command=lambda: sortSize(not reverse))

# Only run if we're on Windows.
if sys.platform == "win32":
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(1) # Fixes blurry font.

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

diskmenu.add_separator()

diskmenu.add_command(label="Format", state=DISABLED)

menubar.add_cascade(label="Disk", menu=diskmenu)

# Create the edit menu.
editmenu = Menu(menubar, tearoff=0)
editmenu.add_command(label="New File", state=DISABLED)
editmenu.add_command(label="New Directory", state=DISABLED)

editmenu.add_separator()

editmenu.add_command(label="Push File", command=pushFile, state=DISABLED)
editmenu.add_command(label="Pull File", command=pullFile, state=DISABLED)

editmenu.add_separator()

editmenu.add_command(label="Copy", state=DISABLED)
editmenu.add_command(label="Rename", command=renameFile, state=DISABLED)
editmenu.add_command(label="Delete", command=deleteFile, state=DISABLED)

menubar.add_cascade(label="Edit", menu=editmenu)

# Create the help menu.
helpmenu = Menu(menubar, tearoff=0)

helpmenu.add_command(label="About", command=lambda: messagebox.showinfo("About", aboutstr))

menubar.add_cascade(label="Help", menu=helpmenu)

# Create the tree view.
tree = ttk.Treeview(root, columns=("size", "time", "date"))
tree.heading("#0", text="File")
tree.heading("size", text="Size", command=lambda: sortSize(False))
tree.heading("time", text="Modified Time")
tree.heading("date", text="Modified Date")

# Create a scrollbar.
sb = ttk.Scrollbar(root, orient="vertical", command=tree.yview)
sb.pack(side="right", fill="y")
tree.configure(yscrollcommand=sb.set)

tree.bind('<ButtonRelease-1>', selectItem)
tree.bind("<Button-3>", showMenu)
tree.bind("<Double-1>", onDoubleClick)

# Run the gui.
tree.pack(expand=True, fill="both")

# Icons for files and folders.
images = {"Folder": ImageTk.PhotoImage(SlitherIcons().getFolder()),
          "File": ImageTk.PhotoImage(SlitherIcons().getFile())}

root.config(menu=menubar)
root.mainloop()
