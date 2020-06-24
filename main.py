#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import subprocess
import sys
import webbrowser
import platform
import logging
import gettext

from PySide2.QtCore import Slot, QSize, SIGNAL
from PySide2.QtGui import QIcon, QDropEvent, QCursor, Qt, QFont, QStandardItem, QStandardItemModel
from PySide2.QtWidgets import (QAction, QApplication, QHeaderView, QHBoxLayout, QLabel, QLineEdit,
                               QMainWindow, QPushButton, QTableWidget, QTableWidgetItem,
                               QVBoxLayout, QWidget, QListWidget, QDialog, QTextEdit, QListWidgetItem, QGroupBox,
                               QComboBox, QMenu, QAbstractItemView, QListView, QSystemTrayIcon, QStyle, QActionGroup,
                               QTableView, QTreeView)

from steamswitcher import SteamSwitcher

i18n = gettext.translation('main', localedir='locales', languages=['en'])
_ = i18n.gettext

#def _(a):
#  return a

class SteamAccountSwitcherGui(QMainWindow):
  account_dialog_window: QDialog
  submit_button: QPushButton
  tray_icon: QSystemTrayIcon
  tray_menu: QMenu

  def __init__(self):
    QMainWindow.__init__(self)
    self.setWindowTitle("Steam Account Switcher")
    self.setMinimumSize(300, 200)
    self.resize(300, 300)

    self.switcher_logo = QIcon("logo.png")
    self.setWindowIcon(self.switcher_logo)
    if platform.system() == "Windows":
      import ctypes
      win_appid = 'github.tommis.steam_account_switcher'
      ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(win_appid)

    self.switcher = SteamSwitcher()
    self.main_widget = QWidget()

    if self.switcher.settings.get("show_on_startup", True):
      self.show()

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

    refresh_action.triggered.connect(self.steamapi_refresh)
    import_action.triggered.connect(lambda: self.import_accounts_dialog())
    open_skinsdir_action.triggered.connect(self.open_skinsdir)
    about_action.triggered.connect(self.about_dialog)
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
    active_behaviour = behaviour_switcher.get(self.switcher.settings["behavior_after_login"], lambda: nothing_behaviour.setChecked(True))
    active_behaviour()

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
    self.accounts_list.customContextMenuRequested.connect(self.show_rightclick_menu)
    #self.accounts_list.layoutChanged.connect(lambda: self.account_reordered)
    #self.accounts_list.dropEvent(self.dropEvent(QDropEvent))

    self.setCentralWidget(self.main_widget)

    if self.switcher.settings.get("use_systemtray"):
      self.tray_icon.show()
    if self.switcher.first_run:
      self.show()
      self.steamapi_key_dialog()
    elif not self.switcher.first_run and \
         not self.is_valid_steampi_key(self.switcher.settings["steam_api_key"]):
      self.tray_icon.showMessage("No api key", "Set the steam web api key.")

  @Slot()
  def exit_app(self):
    self.tray_icon.hide()
    QApplication.quit()

  def show_rightclick_menu(self):
    right_menu = QMenu()

    selected = self.accounts_list.currentItem()
    if not self.accounts_list.selectedItems():
      add_account_action = QAction(_("Add account"), self)
      add_account_action.triggered.connect(lambda: self.account_dialog(True))
      right_menu.addAction(add_account_action)
      right_menu.exec_(QCursor.pos())
      return
    login_name = selected.data(5)
    account = self.switcher.settings["users"].get(login_name, {})

    login_action = QAction(_("Login"), self)
    edit_action = QAction(_("Edit"), self)
    delete_action = QAction(_("Delete"), self)
    open_profile_action = QAction(_("Steam profile"), self)

    delete_action.setIcon(QIcon.fromTheme("edit-delete"))
    open_profile_action.setIcon(QIcon.fromTheme("document-open"))

    right_menu.addActions([login_action, edit_action, delete_action])
    right_menu.addSeparator()
    right_menu.addAction(open_profile_action)

    login_action.triggered.connect(lambda: self.steam_login(login_name))
    edit_action.triggered.connect(lambda: self.account_dialog())
    delete_action.triggered.connect(lambda: self.remove_account(login_name))
    open_profile_action.triggered.connect(lambda: self.open_steam_profile(account))

    open_profile_action.setDisabled(True)
    if account.get("steam_user", {}).get("profileurl"):
      open_profile_action.setEnabled(True)

    if self.accounts_list.selectedItems():
      right_menu.exec_(QCursor.pos())

  def open_steam_profile(self, account):
    webbrowser.open(account["steam_user"].get("profileurl"))

  @Slot()
  def steamapi_refresh(self, uids=None):
    print("Updating")
    try:
      self.switcher.steam_skins = self.switcher.get_steam_skins()
      self.switcher.update_steamuids()
      self.switcher.get_steamapi_usersummary(uids)
      self.load_accounts()
    except Exception as e:
      self.tray_icon.showMessage("Something when wrong updating", str(e))

  @Slot()
  def import_accounts_dialog(self):
    dialog = QDialog(self)
    dialog.setWindowTitle(_("Import accounts"))

    dialog.setMinimumWidth(400)

    layout = QVBoxLayout()
    dialog.setLayout(layout)

    text_label = QLabel(_("Select accounts to import"))
    import_accounts_list = QTreeView()
    import_button = QPushButton()

    model = QStandardItemModel()
    model.setHorizontalHeaderLabels([_('Login name'), _('Steam name'), _('Steam UID')])
    import_accounts_list.setModel(model)
    import_accounts_list.setUniformRowHeights(True)
    import_accounts_list.setEditTriggers(QAbstractItemView.NoEditTriggers)
    import_accounts_list.setSelectionMode(QTreeView.MultiSelection)

    layout.addWidget(text_label)
    layout.addWidget(import_accounts_list)
    layout.addWidget(import_button)

    installed_accounts = self.switcher.settings.get("users").keys()
    disabled = []
    for uid, steam_user in self.switcher.load_loginusers().items():
      account_row = [QStandardItem(steam_user.get("AccountName")),
                     QStandardItem(steam_user.get("PersonaName")),
                     QStandardItem(uid)]
      #account_row[0].setCheckable(True)
      account_row[2].setEnabled(False)

      if steam_user.get("AccountName") in installed_accounts:
        #account_row = [ x.setEnabled(False) for x in account_row]
        disabled.append(account_row)
      else:
        model.appendRow(account_row)

    #model.appendRows(disabled) #Existing accounts grayed out
    import_accounts_list.resizeColumnToContents(0)

    def import_accounts():
      selected_accounts = import_accounts_list.selectionModel().selectedRows()
      for account in selected_accounts:
        self.switcher.add_account(account.data(0))
      self.steamapi_refresh()
      dialog.hide()

    def button_enabled():
      num_selected = len(import_accounts_list.selectionModel().selectedRows())
      import_button.setText(_("Import {0} accounts").format(num_selected))
      if num_selected:
        import_button.setEnabled(True)
      else:
        import_button.setEnabled(False)
    button_enabled()

    import_accounts_list.selectionModel().selectionChanged.connect(button_enabled)
    import_button.clicked.connect(import_accounts)

    dialog.show()

  @Slot()
  def open_skinsdir(self):
    if self.switcher.system_os == "Windows":
        os.startfile(self.switcher.skins_dir)
    elif self.switcher.system_os == "Linux":
        subprocess.Popen(["xdg-open", self.switcher.skins_dir])

  def systemtray(self, parent=None):
    self.tray_icon = QSystemTrayIcon(QIcon("logo.png"))
    self.tray_menu = QMenu(parent)
    self.tray_icon.setToolTip(_("Program to quickly switch between steam accounts"))

    login_menu = QMenu(_("Login with"))
    self.tray_menu.addMenu(login_menu)

    def populate_login_menu():
      login_menu.clear()
      menu_accounts = []
      accounts, avatars = self.load_accounts(no_populate=True)
      if not accounts:
        login_menu.setEnabled(False)
      else:
        login_menu.setEnabled(True)
        for login_name, user in accounts:
          menu_accounts.append(QAction(user.get("steam_name", login_name), self, data=str(login_name)))
          menu_accounts[-1].setToolTip("Login with {0}".format(login_name))
          if self.switcher.settings["show_avatars"]:
            menu_accounts[-1].setIcon(QIcon(avatars.get(login_name, self.switcher.default_avatar)))
          menu_accounts[-1].triggered.connect(lambda: self.steam_login(str(menu_accounts[-1].data()), True))
        login_menu.addActions(menu_accounts)

    def activated(reason):
      if reason == QSystemTrayIcon.Trigger:
        if self.isVisible():
          self.hide()
        else:
          self.show()
      else:
        populate_login_menu()

    self.tray_icon.activated.connect(activated)
    self.tray_menu.addMenu(self.settings_menu)
    self.tray_menu.addSeparator()
    self.tray_menu.addAction(_("Exit"), self.exit_app)
    self.tray_icon.setContextMenu(self.tray_menu)

  @Slot()
  def about_dialog(self):
    dialog = QDialog(self)
    dialog.setWindowTitle("About")

    layout = QVBoxLayout()
    dialog.setLayout(layout)

    text_label = QLabel(_("Steam account switcher<br>"
                        "Author: Tommi Saira &lt;tommi@saira.fi&gt;<br>"
                        "Url: <a href='https://github.com/tommis/steam_account_switcher'>github.com/tommis/steam_account_switcher</a>"))

    text_label.setOpenExternalLinks(True)

    layout.addWidget(text_label)

    dialog.show()

  def is_valid_steampi_key(self, key):
    if len(key) == 32:
      return True
    return False

  @Slot()
  def steamapi_key_dialog(self):
    dialog = QDialog()
    dialog.setWindowTitle(_("Set steamapi key"))
    dialog.setWindowIcon(self.switcher_logo)

    layout = QVBoxLayout()
    dialog.setLayout(layout)

    text_label = QLabel(_("Used for getting avatars. Get yours from <a href='https://steamcommunity.com/dev/apikey'>steam</a>"))
    apikey_edit = QLineEdit()
    save_button = QPushButton(_("Save"))

    text_label.setOpenExternalLinks(True)
    apikey_edit.setText(self.switcher.settings.get("steam_api_key"))

    layout.addWidget(text_label)
    layout.addWidget(apikey_edit)
    layout.addWidget(save_button)

    def save_enabled():
      save_button.setEnabled(self.is_valid_steampi_key(apikey_edit.text()))

    def save():
      self.switcher.settings["steam_api_key"] = apikey_edit.text()
      self.switcher.settings_write()
      dialog.hide()
      if self.switcher.first_run:
        self.import_accounts_dialog()

    save_enabled()

    apikey_edit.textChanged.connect(lambda: save_enabled())
    save_button.clicked.connect(lambda: save())

    dialog.show()

  def dropEvent(self, event):
    print("hallo")

  @Slot()
  def set_show_avatars(self):
    self.switcher.settings["show_avatars"] = not self.switcher.settings.get("show_avatars")
    self.switcher.settings_write()
    self.load_accounts()

  @Slot()
  def set_use_systemtray(self):
    use_systemtray = not self.switcher.settings.get("use_systemtray")
    self.switcher.settings["use_systemtray"] = use_systemtray
    self.switcher.settings_write()
    if use_systemtray:
      self.tray_icon.show()
    else:
      self.tray_icon.hide()

  @Slot()
  def set_after_login_action(self, item):
    self.switcher.settings["behavior_after_login"] = item.data()
    self.switcher.settings_write()

  @Slot()
  def set_size(self, size):
    self.switcher.settings["display_size"] = size
    self.switcher.settings_write()
    self.load_accounts()

  @Slot()
  def account_reordered(self, account):
    print(account)

  def save_account(self, login_name, user, original_login_name = None):
    self.switcher.add_account(login_name, user, original_login_name)

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
    comment_edit.setPlaceholderText(_("Comment"))

    steam_skin_select = QComboBox()
    steam_skin_select.addItems(self.switcher.steam_skins)

    if new_account:
      user = {}
      self.account_dialog_window.setWindowTitle(_("Add account"))
      self.submit_button = QPushButton(_("Add"))
      self.submit_button.setDisabled(True)
    else:

      login_name_selected = self.accounts_list.currentItem().data(5)
      user = self.switcher.settings["users"].get(login_name_selected, {})
      self.account_dialog_window.setWindowTitle(_("Edit account {0}").format(login_name_selected))
      self.submit_button = QPushButton(_("Edit"))
      account_name_edit.setText(login_name_selected)
      comment_edit.setText(user.get("comment"))
      steam_skin_select_index = steam_skin_select.findText(user.get("steam_skin", _("default")))
      if steam_skin_select_index != -1:
        steam_skin_select.setCurrentIndex(steam_skin_select_index)
      else:
        steam_skin_select.setCurrentIndex(1)

    def submit_enabled(item):
      if 3 < len(item) < 32:
        self.submit_button.setEnabled(True)
      else:
        self.submit_button.setEnabled(False)

    account_name_edit.setPlaceholderText(_("Login name"))
    account_name_edit.textChanged.connect(submit_enabled)

    close_button = QPushButton(_("Close"))

    dialog_layout.addWidget(account_name_edit)
    dialog_layout.addWidget(comment_edit)
    dialog_layout.addWidget(steam_skin_select)

    def update_user(user: dict) -> dict:
      user["comment"] = comment_edit.text()
      user["steam_skin"] = steam_skin_select.currentText()
      return user

    self.submit_button.clicked.connect(lambda:self.save_account(account_name_edit.text(),
                                                                update_user(user), login_name_selected if not new_account else None))
    close_button.clicked.connect(self.account_dialog_window.close)

    buttons = QHBoxLayout()
    buttons.addWidget(self.submit_button)
    buttons.addWidget(close_button)

    dialog_layout.addLayout(buttons)

    self.account_dialog_window.show()

  @Slot()
  def steam_login(self, login_name: str, ignore_after_login_behavior=False):
    self.switcher.kill_steam()
    self.switcher.set_autologin_account(login_name)
    self.switcher.start_steam()
    if not ignore_after_login_behavior:
      if self.switcher.settings["behavior_after_login"] == "close":
        self.exit_app()
      elif self.switcher.settings["behavior_after_login"] == "minimize":
        print("minimize to taskbar not implemented")
        self.hide()
      elif self.switcher.settings["behavior_after_login"] == "minimize_tray":
        self.hide()

  def load_accounts(self, no_populate=False):
    sorted_users = sorted(self.switcher.settings["users"].items(), key=lambda a: a[1]["display_order"])
    avatars = self.switcher.get_steam_avatars(list(self.switcher.settings["users"].keys()))
    if not no_populate:
      self.accounts_list.clear()
      self.insert_accounts(sorted_users, avatars)
    else:
      return sorted_users, avatars

  def insert_accounts(self, sorted_users, avatars):
    size = self.switcher.settings.get("display_size", "small")
    font = QFont()
    for login_name, account in sorted_users:
      item = QListWidgetItem()
      item.setData(0, account)
      sname = str(account.get("steam_name", login_name))
      if self.switcher.settings.get("show_avatars"):
        item.setData(1, QIcon(avatars.get(login_name, self.switcher.default_avatar)))
      item.setData(3, account.get("comment"))
      item.setData(5, login_name)
      if size == "small":
        item.setData(2, sname)
        item.setData(13, QSize(0, 20))
        font.setPixelSize(12)
        item.setFont(font)
        self.accounts_list.setIconSize(QSize(20, 20))
      elif size == "medium":
        item.setData(2, sname + "\n" + account.get("comment") if account.get("comment") else sname)
        item.setData(13, QSize(0, 40))
        font.setPixelSize(14)
        item.setFont(font)
        self.accounts_list.setIconSize(QSize(40, 40))
      elif size == "large":
        item.setData(2, sname + "\n" + account.get("comment") if account.get("comment") else sname)
        item.setData(13, QSize(0, 60))
        font.setPixelSize(18)
        item.setFont(font)
        self.accounts_list.setIconSize(QSize(60, 60))
      self.accounts_list.addItem(item)
    #self.switcher.get_steamids()

  def after_steam_login(self):
    """
    Wait for steam to login then run get_steamapi_usersummary
    """
    raise NotImplementedError()


if __name__ == "__main__":
  app = QApplication(sys.argv)
  app.setQuitOnLastWindowClosed(False)

  window = SteamAccountSwitcherGui()

  # Execute application
  sys.exit(app.exec_())