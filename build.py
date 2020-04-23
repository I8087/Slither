import os, sys, shutil
import PyInstaller.__main__

build_scripts = ("slither", "slither_gui")

if sys.platform not in ("win32", "win64"):
    print("Slither doesn't support building on this os!")
    exit(-1)

# Build slither_cmd
PyInstaller.__main__.run(
    ["--clean",
     "--onefile",
     "-nslither",
     "slither_cmd.py"
     ])

# Build slither_gui
PyInstaller.__main__.run(
    ["--clean",
     "--noconsole",
     "--onefile",
     "-nslither_gui",
     "slither_gui.pyw"
     ])

# Clean up spec file.
for i in build_scripts:

    if os.path.exists("{}.spec".format(i)):
        try:
            os.remove("{}.spec".format(i))
        except:
            exit(-1)


# Clean up the __pycache__ and build directory.
for i in (os.path.join(os.getcwd(), "__pycache__"),
          os.path.join(os.getcwd(), "build")):
    if os.path.exists(i):
        try:
            shutil.rmtree(i)
        except:
            exit(-1)

print("Successfully built the programs!...")
