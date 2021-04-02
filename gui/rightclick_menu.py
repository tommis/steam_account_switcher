from PySide2.QtGui import QCursor, QIcon
from PySide2.QtWidgets import QMenu, QAction, QActionGroup

from _i18n import _

class RightClickMenu:
    def show_rightclick_menu(self):
        """

        :type self: SteamAccountSwitcherGui
        """

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
        steampage_menu = QMenu(_("Steam profile"), self)

        edit_action.setIcon(QIcon.fromTheme("document-edit"))
        delete_action.setIcon(QIcon.fromTheme("edit-delete"))
        open_profile_action.setIcon(QIcon.fromTheme("internet-web-browser"))

        right_menu.addActions([login_action, edit_action, delete_action])
        right_menu.addSeparator()
        right_menu.addAction(open_profile_action)
        right_menu.addMenu(steampage_menu)

        login_action.triggered.connect(lambda: self.steam_login(login_name))
        edit_action.triggered.connect(lambda: self.account_dialog())
        delete_action.triggered.connect(lambda: self.remove_account(login_name))

        open_profile_action.triggered.connect(lambda: self.open_steam_profile(account))

        steampage_menu.triggered.connect(lambda: self.open_steam_profile(account))

        steampage_menu_actions = QActionGroup(steampage_menu)
        steampage_menu_inventory = QAction(_('Inventory'), steampage_menu_actions, checkable=True, data="nothing")

        open_profile_action.setDisabled(True)
        if account.get("steam_user", {}).get("profileurl"):
            open_profile_action.setEnabled(True)
            steampage_menu.addActions([steampage_menu_inventory])

        if self.accounts_list.selectedItems():
            right_menu.exec_(QCursor.pos())
