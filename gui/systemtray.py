from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QSystemTrayIcon, QMenu, QAction

from _i18n import _


class SystemTray:
    tray_icon: QSystemTrayIcon
    tray_menu: QMenu

    def set_use_systemtray(self):
        use_systemtray = not self.switcher.settings.get("use_systemtray")
        self.switcher.settings["use_systemtray"] = use_systemtray
        self.switcher.settings_write()
        if use_systemtray:
            self.tray_icon.show()
        else:
            self.tray_icon.hide()

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
