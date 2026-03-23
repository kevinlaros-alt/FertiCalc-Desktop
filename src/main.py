#!/usr/bin/env python3
"""FertiCalc Desktop - Bemestingscalculator."""

import sys
import os

# Ensure src package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ui.app import FertiCalcApp


def main():
    app = FertiCalcApp()
    app.mainloop()


if __name__ == '__main__':
    main()
