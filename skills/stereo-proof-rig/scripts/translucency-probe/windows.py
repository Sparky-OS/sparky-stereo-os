#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# windows.py: three plain windows of known colours for KWin's translucency (inactive window, dialog), each drawn
# opaque by the program, so what shows through on a capture is KWin's opacity alone.
import sys
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication, QDialog, QWidget


def solid(w, colour, title):
    pal = w.palette()
    pal.setColor(QPalette.ColorRole.Window, QColor(colour))
    w.setPalette(pal)
    w.setAutoFillBackground(True)
    w.setWindowTitle(title)
    return w


app = QApplication(sys.argv)
a = solid(QWidget(), "#c03030", "probe-inactive"); a.resize(420, 260); a.show()
b = solid(QWidget(), "#30a040", "probe-active"); b.resize(420, 260); b.show()
d = solid(QDialog(b), "#3050c0", "probe-dialog"); d.resize(300, 180); d.show()
sys.exit(app.exec())
