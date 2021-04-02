from PySide2.QtCore import QSize
from PySide2.QtGui import QIcon, QFont
from PySide2.QtWidgets import QListWidgetItem

from _i18n import _


class Accounts:
  def steamapi_refresh(self, uids=None):
    print("Updating")
    try:
        self.switcher.steam_skins = self.switcher.get_steam_skins()
        self.switcher.update_steamuids()
        self.switcher.get_steamapi_usersummary(uids)
        self.load_accounts()
    except Exception as e:
        self.tray_icon.showMessage(_("ERROR"), _("Something when wrong updating \n{0}").format(str(e)),
                                   self.switcher_logo)

  def account_reordered(self, account):
    print(account)

  def save_account(self, login_name, user, original_login_name = None):
    self.switcher.add_account(login_name, user, original_login_name)

    self.load_accounts()
    self.account_dialog_window.close()

  def remove_account(self, account_name):
    self.switcher.delete_account(account_name)
    self.load_accounts()

  def steam_login(self, login_name: str, ignore_after_login_behavior=False):
    try:
      self.switcher.login_with(login_name)
    except PermissionError:
      self.tray_icon.showMessage(_("Permission error"), _("Are you running as administrator?"), self.switcher_logo)

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

    def insert(name, qsize, font_size: int, icon_size):
      item.setData(2, name)
      item.setData(13, qsize)
      font.setPixelSize(font_size)
      item.setFont(font)
      self.accounts_list.setIconSize(icon_size)

    for login_name, account in sorted_users:
      item = QListWidgetItem()
      item.setData(0, account)
      sname = str(account.get("steam_name", login_name))
      if self.switcher.settings.get("show_avatars"):
        item.setData(1, QIcon(avatars.get(login_name, self.switcher.default_avatar)))
      item.setData(3, account.get("comment"))
      item.setData(5, login_name)
      if size == "small":
        insert(sname, QSize(0, 20), 12, QSize(20, 20))
      elif size == "medium":
        insert(sname + "\n" + account.get("comment") if account.get("comment") else sname,
               QSize(0, 40), 14, QSize(40, 40))
      elif size == "large":
        insert(sname + "\n" + account.get("comment") if account.get("comment") else sname,
               QSize(0, 60), 18, QSize(60, 60))
      self.accounts_list.addItem(item)
    #self.switcher.get_steamids()

  def after_steam_login(self):
    """
    Wait for steam to login then run get_steamapi_usersummary
    """
    raise NotImplementedError()