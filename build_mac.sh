#!/bin/bash
# Build FertiCalc for Mac
# Requires: pip install pyinstaller
pyinstaller --onefile --windowed \
    --name FertiCalc \
    --add-data "FertiCalc_data.xlsx:." \
    src/main.py

echo "Build complete! Find FertiCalc.app in dist/"
