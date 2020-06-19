#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import subprocess
import sys
import webbrowser
import platform
import logging

from PySide2.QtCore import Slot, QSize
from PySide2.QtGui import QIcon, QDropEvent, QCursor, Qt
from PySide2.QtWidgets import (QAction, QApplication, QHeaderView, QHBoxLayout, QLabel, QLineEdit,
                               QMainWindow, QPushButton, QTableWidget, QTableWidgetItem,
                               QVBoxLayout, QWidget, QListWidget, QDialog, QTextEdit, QListWidgetItem, QGroupBox,
                               QComboBox, QMenu, QAbstractItemView, QListView, QSystemTrayIcon)

from steamswitcher import SteamSwitcher


class SteamAccountSwitcherGui(QMainWindow):
  account_dialog_window: QDialog
  submit_button: QPushButton
  tray_icon: QSystemTrayIcon
  tray_menu: QMenu

  def __init__(self):
    QMainWindow.__init__(self)
    self.setWindowTitle("Steam Account Switcher")
    self.setMinimumHeight(300)
    self.setMinimumWidth(300)
    self.setMaximumWidth(300)

    switcher_logo = QIcon("logo.png")
    self.setWindowIcon(switcher_logo)
    if platform.system() == "Windows":
      import ctypes
      win_appid = 'github.tommis.steam_account_switcher.alpha'
      ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(win_appid)

    # Menu
    self.menu = self.menuBar()
    self.file_menu = self.menu.addMenu("File")
    self.size_menu = self.menu.addMenu("Size")

    settings_action = QAction("Settings", self, )
    settings_action.triggered.connect(self.settings_dialog)
    refresh_action = QAction("refresh", self)
    refresh_action.triggered.connect(self.steamapi_refresh)
    open_skinsdir_action = QAction("Skins dir", self)
    open_skinsdir_action.triggered.connect(self.open_skinsdir)
    about_action = QAction("About", self)
    about_action.triggered.connect(self.about_dialog)
    exit_action = QAction("Exit", self)
    exit_action.triggered.connect(self.exit_app)

    refresh_action.setShortcut("F5")
    exit_action.setShortcut("Ctrl+Q")

    self.file_menu.addAction(settings_action)
    self.file_menu.addAction(refresh_action)
    self.file_menu.addAction(open_skinsdir_action)
    self.file_menu.addAction(about_action)
    self.file_menu.addSeparator()
    self.file_menu.addAction(exit_action)

    set_size_large = QAction("Large", self)
    set_size_medium = QAction("Medium", self)
    set_size_small = QAction("Small", self)
    set_size_large.triggered.connect(lambda: self.set_size("large"))
    set_size_medium.triggered.connect(lambda: self.set_size("medium"))
    set_size_small.triggered.connect(lambda: self.set_size("small"))
    self.size_menu.addAction(set_size_large)
    self.size_menu.addAction(set_size_medium)
    self.size_menu.addAction(set_size_small)

    set_size_large.setShortcut("Ctrl+1")
    set_size_medium.setShortcut("Ctrl+2")
    set_size_small.setShortcut("Ctrl+3")

    self.add_button = QPushButton("Add account")
    self.edit_button = QPushButton("Edit account")
    self.edit_button.setDisabled(1)

    self.buttons = QHBoxLayout()
    self.buttons.addWidget(self.add_button)
    self.buttons.addWidget(self.edit_button)

    self.main_widget = QWidget()
    self.layout = QVBoxLayout()
    self.main_widget.setLayout(self.layout)

    self.layout.setSpacing(10)

    self.accounts_list = QListWidget()
    self.accounts_list.selectionMode()
    self.accounts_list.setDragDropMode(QAbstractItemView.InternalMove)
    self.layout.addWidget(self.accounts_list)
    self.layout.addLayout(self.buttons)

    self.switcher = SteamSwitcher()
    self.load_accounts()

    # Signals and Slots
    self.add_button.clicked.connect(lambda: self.account_dialog(True))
    self.edit_button.clicked.connect(lambda: self.account_dialog(False))
    self.accounts_list.itemSelectionChanged.connect(self.edit_button_enabled)
    self.accounts_list.doubleClicked.connect(self.steam_login)
    #self.accounts_list.dragMoveEvent.connect()
    self.accounts_list.setContextMenuPolicy(Qt.CustomContextMenu)
    self.accounts_list.customContextMenuRequested.connect(self.show_rightclick_menu)
    #self.accounts_list.layoutChanged.connect(self.account_reordered)

    # System tray
    if self.switcher.settings.get("use_systemtray"):
      self.systemtray(self.main_widget)

    self.setCentralWidget(self.main_widget)

    self.show()

  @Slot()
  def exit_app(self):
    self.tray_icon.hide()
    QApplication.quit()

  def show_rightclick_menu(self, item):
    right_menu = QMenu(self.accounts_list)

    selected = self.accounts_list.currentItem()
    login_name = selected.data(5)
    account = self.switcher.settings["users"].get(login_name, {})

    login_action = QAction("Login", self)
    edit_action = QAction("Edit", self)
    delete_action = QAction("Delete", self)
    open_profile_action = QAction("Steam profile", self)

    delete_action.setIcon(QIcon.fromTheme("edit-delete"))
    open_profile_action.setIcon(QIcon.fromTheme("document-open"))

    right_menu.addAction(login_action)
    right_menu.addAction(edit_action)
    right_menu.addAction(delete_action)
    right_menu.addSeparator()
    right_menu.addAction(open_profile_action)

    login_action.triggered.connect(lambda: self.steam_login(selected))
    edit_action.triggered.connect(lambda: self.account_dialog())
    delete_action.triggered.connect(lambda: self.remove_account(login_name))
    open_profile_action.triggered.connect(lambda: self.open_steam_profile(account))

    open_profile_action.setDisabled(True)
    if account.get("steam_user", {}).get("profileurl"):
      open_profile_action.setEnabled(True)

    right_menu.exec_(QCursor.pos())

  def open_steam_profile(self, account):
    webbrowser.open(account["steam_user"].get("profileurl"))

  @Slot()
  def steamapi_refresh(self):
    self.switcher.steam_skins = self.switcher.get_steam_skins()
    self.switcher.get_steamuids()
    self.switcher.get_steamapi_usersummary()
    self.load_accounts()

  @Slot()
  def settings_dialog(self):
    logging.info("Opened settings")
    raise NotImplementedError("settings not done yet")

  @Slot()
  def open_skinsdir(self):
    if self.switcher.system_os == "Windows":
        os.startfile(self.switcher.skins_dir)
    elif self.switcher.system_os == "Linux":
        subprocess.Popen(["xdg-open", self.switcher.skins_dir])

  def systemtray(self, parent=None):
    self.tray_icon = QSystemTrayIcon(QIcon("logo.png"), parent)
    self.tray_menu = QMenu(parent)
    self.tray_menu.addAction("Open", self.show)
    self.tray_menu.addSeparator()
    self.tray_menu.addAction("Exit", self.exit_app)
    self.tray_icon.setContextMenu(self.tray_menu)
    self.tray_icon.show()

  @Slot()
  def about_dialog(self):
    dialog = QDialog(self)
    dialog.setWindowTitle("About")
    dialog.setFixedSize(220, 60)

    layout = QVBoxLayout()
    dialog.setLayout(layout)

    text_label = QLabel("Steam account switcher\nAuthor: Tommi Saira <tommi@saira.fi>\nUrl: github.com")
    layout.addWidget(text_label)

    dialog.show()

  @Slot()
  def set_size(self, size):
    print("Set size {0}".format(size))
    self.switcher.settings["display_size"] = size
    self.switcher.settings_write()
    self.load_accounts()

  @Slot()
  def account_reordered(self, account):
    print(account)

  @Slot()
  def edit_button_enabled(self):
    if self.accounts_list.selectedItems():
      self.edit_button.setEnabled(True)
    else:
      self.edit_button.setEnabled(False)

  @Slot()
  def submit_enabled(self, item):
    if len(item) > 3:
      self.submit_button.setEnabled(True)
    else:
      self.submit_button.setEnabled(False)

  def save_account(self, new_account, account_name, old_account_name, comment, steam_skin):
    self.switcher.add_new_account(account_name, "" if new_account else old_account_name, comment, steam_skin)

    self.load_accounts()
    self.account_dialog_window.close()

  def remove_account(self, account_name):
    self.switcher.delete_account(account_name)
    self.load_accounts()


  @Slot()
  def account_dialog(self, new_account=False):
    self.account_dialog_window = QDialog(self)
    self.account_dialog_window.setMinimumSize(300, 125)

    # Main layout
    dialog_layout = QVBoxLayout()
    self.account_dialog_window.setLayout(dialog_layout)

    account_name_edit = QLineEdit()

    comment_edit = QLineEdit()
    comment_edit.setPlaceholderText("Comment")

    steam_skin_select = QComboBox()
    steam_skin_select.addItems(self.switcher.steam_skins)

    login_name = self.accounts_list.currentItem().data(5)
    user = self.switcher.settings["users"].get(self.accounts_list.currentItem().data(5), {})

    if new_account:
      self.account_dialog_window.setWindowTitle("Add account")
      self.submit_button = QPushButton("Add")
      self.submit_button.setDisabled(True)
    else:

      self.account_dialog_window.setWindowTitle("Edit account {0}".format(login_name))
      self.submit_button = QPushButton("Edit")
      account_name_edit.setText(login_name)
      comment_edit.setText(user.get("comment"))
      steam_skin_select_index = steam_skin_select.findText(user.get("steam_skin", "default"))
      if steam_skin_select_index != -1:
        steam_skin_select.setCurrentIndex(steam_skin_select_index)
      else:
        steam_skin_select.setCurrentIndex(1)

    account_name_edit.setPlaceholderText("Login name")
    account_name_edit.textChanged.connect(self.submit_enabled)


    close_button = QPushButton("Close")

    dialog_layout.addWidget(account_name_edit)
    dialog_layout.addWidget(comment_edit)
    dialog_layout.addWidget(steam_skin_select)

    user["steam_skin"] = steam_skin_select.currentText()

    self.submit_button.clicked.connect(lambda: self.save_account(
      new_account, account_name_edit.text(), "" if new_account else login_name,
      comment_edit.text(), steam_skin_select.currentText()))
    close_button.clicked.connect(self.account_dialog_window.close)

    buttons = QHBoxLayout()
    buttons.addWidget(self.submit_button)
    buttons.addWidget(close_button)

    dialog_layout.addLayout(buttons)

    self.account_dialog_window.show()

  @Slot()
  def steam_login(self, item):
    self.switcher.kill_steam()
    self.switcher.set_autologin_account(item.data(0))
    self.switcher.start_steam()
    if self.switcher.settings["behavior_after_login"] == "close":
      self.exit_app()
    elif self.switcher.settings["behavior_after_login"] == "minimize":
      self.hide()


  def load_accounts(self):
    self.accounts_list.clear()
    sorted_users = sorted(self.switcher.settings["users"].items(), key=lambda a: a[1]["display_order"])
    avatars = self.switcher.get_steam_avatars(list(self.switcher.settings["users"].keys()))
    self.insert_accounts(sorted_users, avatars)

  def insert_accounts(self, sorted_users, avatars):
    size = self.switcher.settings.get("display_size", "small")
    for login_name, account in sorted_users:
      item = QListWidgetItem()
      item.setData(0, account)
      if self.switcher.settings.get("show_avatars"):
        item.setData(1, QIcon(avatars.get(login_name)))
      item.setData(2, str(account.get("steam_name", login_name)))
      item.setData(3, account.get("comment"))
      item.setData(5, login_name)
      if size == "small":
        item.setData(13, QSize(0, 20))
      if size == "medium":
        item.setData(13, QSize(0, 40))
      if size == "large":
        item.setData(13, QSize(0, 60))
      self.accounts_list.addItem(item)
    #self.switcher.get_steamids()

  def after_steam_login(self):
    """
    Wait for steam to login then run get_steamapi_usersummary
    """
    raise NotImplementedError()


if __name__ == "__main__":
  app = QApplication(sys.argv)

  window = SteamAccountSwitcherGui()

  # Execute application
  sys.exit(app.exec_())