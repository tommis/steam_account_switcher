import gettext
import os
import signal
import subprocess
import sys
import webbrowser
import platform
import logging
from typing import Union

if 'PySide2' in sys.modules:
  from PySide2.QtCore import Slot, QSize, SIGNAL
  from PySide2.QtGui import QIcon, QDropEvent, QCursor, Qt, QFont, QStandardItem, QStandardItemModel
  from PySide2.QtWidgets import (QMainWindow, QAction, QApplication, QHeaderView, QHBoxLayout, QLabel, QLineEdit,
                                 QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QListWidget,
                                 QDialog, QTextEdit, QListWidgetItem, QGroupBox, QComboBox, QMenu, QAbstractItemView,
                                 QListView, QSystemTrayIcon, QStyle, QActionGroup, QTableView, QTreeView)
elif 'PyQt5' in sys.modules:
  pass
  #from PyQt5 import QtGui, QtWidgets, QtCore
  #from PyQt5.QtCore import pyqtSignal as Signal, pyqtSlot as Slot
else:
  print("Pyside2 or PyQt5 should be installed")

from _i18n import _

from accounts import Accounts
from dialog_about import DialogAbout
from dialog_account import DialogAccount
from dialog_import_accounts import DialogImportAccount
from dialog_steamapi_key import DialogSteamapiKey
from rightclick_menu import RightClickMenu
from settings import Settings
from systemtray import SystemTray

class SteamAccountSwitcherGui(QMainWindow, Accounts, DialogAccount, DialogImportAccount, DialogSteamapiKey, Settings, SystemTray):
  account_dialog_window: QDialog
  submit_button: QPushButton
  tray_menu: QMenu

  def __init__(self):
    QMainWindow.__init__(self)
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    self.setWindowTitle("Steam Account Switcher")
    self.setMinimumSize(300, 200)
    self.resize(300, 300)

    # Logo
    self.switcher_logo = QIcon("logo.png")
    self.setWindowIcon(self.switcher_logo)
    if platform.system() == "Windows":  # windows taskbar app icon fix
      import ctypes
      win_appid = 'github.tommis.steam_account_switcher'
      ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(win_appid)

    from steamswitcher import SteamSwitcher

    import gui.rightclick_menu
    import gui.systemtray


    self.switcher = SteamSwitcher()
    self.args = self.switcher.args
    self.main_widget = QWidget()

    if self.args.gui or self.switcher.settings.get("show_on_startup", True) and not self.args.no_gui:
      self.show()
    elif self.args.no_gui and self.args.no_tray:
      self.exit_app()

    # Menu
    self.menu = self.menuBar()
    self.file_menu = self.menu.addMenu(_("File"))
    self.settings_menu = self.menu.addMenu(_("Settings"))
    self.size_menu = self.menu.addMenu(_("Size"))

    refresh_action = QAction(_("Refresh"), self)
    import_action = QAction(_("Import accounts"), self)
    open_skinsdir_action = QAction(_("Skins dir"), self)
    about_action = QAction(_("About"), self)
    exit_action = QAction(_("Exit"), self)

    refresh_action.triggered.connect(Accounts.steamapi_refresh)
    import_action.triggered.connect(lambda: DialogImportAccount.import_accounts_dialog(self))
    open_skinsdir_action.triggered.connect(self.open_skinsdir)
    about_action.triggered.connect(lambda: DialogAbout.about_dialog(self))
    exit_action.triggered.connect(self.exit_app)

    refresh_action.setShortcut("F5")
    exit_action.setShortcut("Ctrl+Q")

    self.file_menu.addActions([refresh_action, import_action, open_skinsdir_action, about_action])
    self.file_menu.addSeparator()
    self.file_menu.addAction(exit_action)

    set_steamapi_key = QAction(_("Set steamapi key"), self)
    show_avatars = QAction(_("Show avatars"), self, checkable=True)
    use_systemtray = QAction(_("Use systemtray"), self, checkable=True)

    after_login_menu = QMenu(_("After login"))

    after_login_behaviour_group = QActionGroup(after_login_menu)
    nothing_behaviour = QAction(_('Nothing'), after_login_behaviour_group, checkable=True, data="nothing")
    close_behaviour = QAction(_('Close'), after_login_behaviour_group, checkable=True, data="close")
    minimize_behaviour = QAction(_('Minimize to taskbar'), after_login_behaviour_group, checkable=True, data="minimize")
    minimize_tray_behaviour = QAction(_('Minimize to tray'), after_login_behaviour_group, checkable=True, data="minimize_tray")

    after_login_menu.addActions([nothing_behaviour, close_behaviour, minimize_behaviour, minimize_tray_behaviour])

    behaviour_switcher = {
      "close": lambda: close_behaviour.setChecked(True),
      "minimize": lambda: minimize_behaviour.setChecked(True),
      "minimize_tray": lambda: minimize_tray_behaviour.setChecked(True)
    }
    behaviour_switcher.get(self.switcher.settings["behavior_after_login"], lambda: nothing_behaviour.setChecked(True))()

    after_login_menu.triggered.connect(self.set_after_login_action)


    self.systemtray(self.main_widget)

    set_steamapi_key.triggered.connect(lambda: self.steamapi_key_dialog())
    show_avatars.triggered.connect(lambda: self.set_show_avatars())
    use_systemtray.triggered.connect(lambda: self.set_use_systemtray())

    self.settings_menu.addAction(set_steamapi_key)
    self.settings_menu.addSeparator()
    self.settings_menu.addActions([show_avatars, use_systemtray])
    self.settings_menu.addMenu(after_login_menu)

    show_avatars.setChecked(self.switcher.settings.get("show_avatars"))
    use_systemtray.setChecked(self.switcher.settings.get("use_systemtray"))

    set_size_small = QAction(_("Small"), self)
    set_size_medium = QAction(_("Medium"), self)
    set_size_large = QAction(_("Large"), self)
    set_size_small.triggered.connect(lambda: self.set_size("small"))
    set_size_medium.triggered.connect(lambda: self.set_size("medium"))
    set_size_large.triggered.connect(lambda: self.set_size("large"))
    self.size_menu.addActions([set_size_small, set_size_medium, set_size_large])

    set_size_small.setShortcut("Ctrl+1")
    set_size_medium.setShortcut("Ctrl+2")
    set_size_large.setShortcut("Ctrl+3")

    self.add_button = QPushButton(_("Add account"))
    self.edit_button = QPushButton(_("Edit account"))
    self.edit_button.setDisabled(True)

    self.buttons = QHBoxLayout()
    self.buttons.addWidget(self.add_button)
    self.buttons.addWidget(self.edit_button)

    self.layout = QVBoxLayout()
    self.main_widget.setLayout(self.layout)

    self.accounts_list = QListWidget()
    self.accounts_list.setDragDropMode(QAbstractItemView.InternalMove)
    self.layout.addWidget(self.accounts_list)
    self.layout.addLayout(self.buttons)

    self.layout.setSpacing(10)
    self.accounts_list.setSpacing(1)

    self.import_accounts_window = QDialog()

    self.load_accounts()

    def edit_button_enabled():
      if self.accounts_list.selectedItems():
        self.edit_button.setEnabled(True)
      else:
        self.edit_button.setEnabled(False)

    # Signals and Slots
    self.add_button.clicked.connect(lambda: self.account_dialog(True))
    self.edit_button.clicked.connect(lambda: self.account_dialog(False))
    self.accounts_list.itemSelectionChanged.connect(edit_button_enabled)
    self.accounts_list.doubleClicked.connect(lambda: self.steam_login(self.accounts_list.currentIndex().data(5)))
    self.accounts_list.setContextMenuPolicy(Qt.CustomContextMenu)
    self.accounts_list.customContextMenuRequested.connect(lambda: RightClickMenu.show_rightclick_menu(self))
    #self.accounts_list.layoutChanged.connect(lambda: self.account_reordered)
    #self.accounts_list.dropEvent(self.dropEvent(QDropEvent))

    self.setCentralWidget(self.main_widget)

    if self.args.no_tray:
      print("test")
    elif self.switcher.settings.get("use_systemtray") or self.args.tray:
      self.tray_icon.show()

    if self.switcher.first_run or self.args.first_run:
      self.steamapi_key_dialog()
    elif not self.switcher.first_run and \
         not self.is_valid_steampi_key(self.switcher.settings["steam_api_key"]):
      self.tray_icon.showMessage("No api key", "Set the steam web api key.", self.switcher_logo)

  def exit_app(self):
    self.tray_icon.hide()
    QApplication.quit()

  def open_steam_profile(self, account, ):
    webbrowser.open(account["steam_user"].get("profileurl"))

  def open_skinsdir(self):
    if self.switcher.system_os == "Windows":
        os.startfile(self.switcher.skins_dir)
    elif self.switcher.system_os == "Linux":
        subprocess.Popen(["xdg-open", self.switcher.skins_dir])

  def dropEvent(self, event):
    print("hallo")

  def set_stay_on_top(self):
    pass


