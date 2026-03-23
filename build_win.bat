@echo off
REM Build FertiCalc for Windows
REM Requires: pip install pyinstaller
pyinstaller --onefile --windowed ^
    --name FertiCalc ^
    --add-data "FertiCalc_data.xlsx;." ^
    src/main.py

echo Build complete! Find FertiCalc.exe in dist\
