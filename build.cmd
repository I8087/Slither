@echo off
rem A simple windows build script for Slither. Requires PyInstaller
pyinstaller --clean --onefile slither_cmd.py
rmdir /S /Q build
rmdir /S /Q __pycache__
pause
