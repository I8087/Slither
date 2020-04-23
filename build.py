#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os, sys, shutil
import PyInstaller.__main__

build_scripts = ("slither", "slither_gui")

if sys.platform not in ("win32", "win64", "linux"):
    print("Slither doesn't support building on this os!")
    exit(-1)

# Build slither_cmd
PyInstaller.__main__.run(
    ["--clean",
     "--onefile",
     "-nslither",
     os.path.join(os.getcwd(), "src", "slither_cmd.py")
     ])

# Build slither_gui
PyInstaller.__main__.run(
    ["--clean",
     "--noconsole",
     "--onefile",
     "--hidden-import=PIL._tkinter_finder",
     "-nslither_gui",
     os.path.join(os.getcwd(), "src", "slither_gui.pyw")
     ])

# Clean up spec file.
for i in build_scripts:

    if os.path.exists("{}.spec".format(i)):
        try:
            os.remove("{}.spec".format(i))
        except:
            exit(-1)


# Clean up the __pycache__ and build directory.
for i in (os.path.join(os.getcwd(), "src", "__pycache__"),
          os.path.join(os.getcwd(), "build")):
    if os.path.exists(i):
        try:
            shutil.rmtree(i)
        except:
            exit(-1)

# Make a build directory.
os.mkdir(os.path.join(os.getcwd(), "build"))

# Move over the programs into the build directory.
for i in build_scripts:
    if sys.platform[:3] == "win":
        i += ".exe"
        shutil.copy2(os.path.join(os.getcwd(), "dist", i),
                     os.path.join(os.getcwd(), "build", i))

# Move the rest of the required files into the dist directory.
# They will be bundled together into one archive.
for i in ("CHANGELOG.md", "LICENSE", "README.md"):
    shutil.copy2(os.path.join(os.getcwd(), i),
                 os.path.join(os.getcwd(), "dist", i))

# Archive the programs.
    if sys.platform[:3] == "win":
        arch_format = "zip"
    else:
        arch_format = "gztar"

shutil.make_archive(os.path.join(os.getcwd(), "build", "Slither-{}".format(sys.platform)), arch_format, "dist")

# Remove the dist directory.
if os.path.exists("dist"):
    try:
        shutil.rmtree("dist")
    except:
        exit(-1)


print("Successfully built the programs!...")
