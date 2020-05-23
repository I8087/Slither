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

class SlitherGUI(Frame):
    def __init__(self, parent, *args, **kwargs):
        self.parent = parent
        self.parent.title("Slither - []")
        self.checkDPI()
        Frame.__init__(self, parent, *args, **kwargs)
        self.addMenubar()
        self.addTree()

        # Icons for files and folders.
        self.images = {"Folder": ImageTk.PhotoImage(SlitherIcons().getFolder()),
                       "File": ImageTk.PhotoImage(SlitherIcons().getFile())}

        # Let Slither know that the gui is running.
        self.SLITHER_GUI = True

        self.slither_cmd = Slither_CMD("")

    def checkDPI(self):
        #Only run if on Windows.
        if sys.platform[:3] == "win":
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1) # Fixes blurry font.

    def addMenubar(self):
        # Create the menu bar.
        self.menubar = Menu(self)

        # Create the file menu.
        self.filemenu = Menu(self.menubar, tearoff=0)
        self.filemenu.add_command(label="New", state=DISABLED)
        self.filemenu.add_command(label="Mount", command=self.mountDisk)
        self.filemenu.add_command(label="Unmount", command=self.unmountDisk, state=DISABLED)

        self.filemenu.add_separator()

        self.filemenu.add_command(label="Exit", command=self.parent.quit)

        self.menubar.add_cascade(label="File", menu=self.filemenu)

        # Create the disk menu.
        self.diskmenu = Menu(self.menubar, tearoff=0)

        self.diskmenu.add_command(label="Info", state=DISABLED)
        self.diskmenu.add_command(label="Space", state=DISABLED)

        self.diskmenu.add_separator()

        self.diskmenu.add_command(label="Format", state=DISABLED)

        self.menubar.add_cascade(label="Disk", menu=self.diskmenu)

        # Create the edit menu.
        self.editmenu = Menu(self.menubar, tearoff=0)
        self.editmenu.add_command(label="New File", state=DISABLED)
        self.editmenu.add_command(label="New Directory", state=DISABLED)

        self.editmenu.add_separator()

        self.editmenu.add_command(label="Push File", command=self.pushFile, state=DISABLED)
        self.editmenu.add_command(label="Pull File", command=self.pullFile, state=DISABLED)

        self.editmenu.add_separator()

        self.editmenu.add_command(label="Copy", state=DISABLED)
        self.editmenu.add_command(label="Rename", command=self.renameFile, state=DISABLED)
        self.editmenu.add_command(label="Delete", command=self.deleteFile, state=DISABLED)

        self.menubar.add_cascade(label="Edit", menu=self.editmenu)

        # Create the help menu.
        self.helpmenu = Menu(self.menubar, tearoff=0)

        self.helpmenu.add_command(label="About", command=lambda: messagebox.showinfo("About", aboutstr))

        self.menubar.add_cascade(label="Help", menu=self.helpmenu)

        self.parent.config(menu=self.menubar)

    def addTree(self):
        # Create the tree view.
        self.tree = ttk.Treeview(self.parent, columns=("size", "time", "date"))
        self.tree.heading("#0", text="File")
        self.tree.heading("size", text="Size", command=lambda: self.sortSize(False))
        self.tree.heading("time", text="Modified Time")
        self.tree.heading("date", text="Modified Date")

        # Create a scrollbar.
        sb = ttk.Scrollbar(self.parent, orient="vertical", command=self.tree.yview)
        sb.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=sb.set)

        self.tree.bind('<ButtonRelease-1>', self.selectItem)
        self.tree.bind("<Button-3>", self.showMenu)
        self.tree.bind("<Double-1>", self.onDoubleClick)

        # Run the gui.
        self.tree.pack(expand=True, fill="both")


    def onDoubleClick(self, event):
        curItem = self.tree.item(self.tree.focus())

        e = self.slither_cmd.disk.getDir()
        e_dir = [i for i in e if e[i]["IS_DIRECTORY"]]

        if curItem["text"] in e_dir:
            self.slither_cmd.do_cd((curItem["text"],))
            self.refreshTree()

    # show the menu bar with a right click.
    def showMenu(self, event):

        r = self.tree.identify_row(event.y)
        if r:
            self.tree.focus(r)
            self.tree.selection_set(r)

        self.selectItem(event)
        self.menubar.post(event.x_root, event.y_root)

    def selectItem(self, event):
        curItem = self.tree.focus()
        if curItem:
            #self.editmenu.entryconfigure("Copy", state=NORMAL)
            self.editmenu.entryconfigure("Rename", state=NORMAL)
            self.editmenu.entryconfigure("Delete", state=NORMAL)
            self.editmenu.entryconfigure("Pull File", state=NORMAL)

    def deselectItem(self):
        self.editmenu.entryconfigure("Copy", state=DISABLED)
        self.editmenu.entryconfigure("Rename", state=DISABLED)
        self.editmenu.entryconfigure("Delete", state=DISABLED)
        self.editmenu.entryconfigure("Pull File", state=DISABLED)

    def deleteFile(self):
        curItem = self.tree.item(self.tree.focus())
        if messagebox.askquestion("Delete", "Are you sure you want to delete \'%s\'?" % curItem["text"], icon="warning") == "yes":
            self.slither_cmd.do_del((curItem["text"],))
            self.refreshTree()

    def renameFile(self):
        curItem = self.tree.item(self.tree.focus())
        a = simpledialog.askstring("Rename", "Input the new file name:")
        if a:
            self.slither_cmd.do_ren((curItem["text"], a))
            self.refreshTree()

    def pullFile(self):
        curItem = self.tree.item(self.tree.focus())
        #filename = filedialog.asksaveasfilename(initialdir = ".", title = "Save File")
        self.slither_cmd.do_pull((curItem["text"],))

    def pushFile(self):
        filename = filedialog.askopenfilename(initialdir = ".", title = "Select File")
        self.slither_cmd.do_push((filename,))
        self.refreshTree()

    def mountDisk(self):
        filename = filedialog.askopenfilename(initialdir = ".", title = "Select Disk",filetypes = (("Virtual Floppy Disk", ("*.dmg", "*.flp", "*.vfd")), ("all files", "*.*")))
        self.slither_cmd.do_mount((filename,))

        if self.slither_cmd.disk.isMounted():
            self.filemenu.entryconfigure("Mount", state=DISABLED)
            self.filemenu.entryconfigure("Unmount", state=NORMAL)
            self.editmenu.entryconfigure("Push File", state=NORMAL)
            self.parent.title("Slither - [%s]" % filename)
            self.refreshTree()

    def unmountDisk(self):
            self.slither_cmd.do_unmount(tuple())
            self.filemenu.entryconfigure("Unmount", state = DISABLED)
            self.filemenu.entryconfigure("Mount", state = NORMAL)
            self.editmenu.entryconfigure("Push File", state=DISABLED)
            self.deselectItem()
            self.parent.title("Slither - []")
            self.tree.delete(*self.tree.get_children())

    def refreshTree(self):
        self.tree.delete(*self.tree.get_children())

        e = self.slither_cmd.disk.getDir()
        dis_dir = [i for i in e if e[i]["IS_DIRECTORY"]]
        dis_files = [i for i in e if e[i]["IS_FILE"]]

        for i in sorted(dis_dir, key=str.lower):

            self.tree.insert("",
                             "end",
                             text=i,
                             values=("", e[i]["MODIFIED_TIME_STR"], e[i]["MODIFIED_DATE_STR"]),
                             image=self.images["Folder"])


        for i in sorted(dis_files, key=str.lower):

            # Get appropriate size.
            b = e[i]["SIZE"]
            pf = "B"
            if b > 1024:
                b = b // 1024
                pf = "KiB"

            self.tree.insert("",
                             "end",
                             text=i,
                             values=("{} {}".format(b, pf), e[i]["MODIFIED_TIME_STR"], e[i]["MODIFIED_DATE_STR"]),
                             image=self.images["File"])

    def sortSize(self, reverse):
        l = []

        for i in self.tree.get_children(""):
            s = self.tree.set(i, "size").split()
            s[0] = int(s[0])

            if s[1] == "KiB":
                s[0] *= 1024

            l.append((s[0], i))
            
        l.sort(reverse=reverse)

        for index, (val, i) in enumerate(l):
            self.tree.move(i, "", index)

        # reverse sort next time
        self.tree.heading("size", text="Size", command=lambda: self.sortSize(not reverse))

if __name__ == "__main__":
    root = Tk()
    SlitherGUI(root).pack(side="top", fill="both", expand=True)
    root.mainloop()
