#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys

from PySide2.QtWidgets import QApplication

import gui

if __name__ == "__main__":
  app = QApplication(sys.argv)
  app.setQuitOnLastWindowClosed(False)

  window = gui.SteamAccountSwitcherGui()

  sys.exit(app.exec_()) # Execute application
