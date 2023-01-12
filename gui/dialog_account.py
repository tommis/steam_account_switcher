from PySide2.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QComboBox, QPushButton, QHBoxLayout

from ._i18n import _


class DialogAccount:
    account_dialog_window: QDialog

    def account_dialog(self, new_account=False):
        self.account_dialog_window = QDialog(self)
        self.account_dialog_window.setMinimumSize(300, 125)
        if self.account_dialog_window.isVisible():
            self.account_dialog_window.hide()

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

        def update_user(u: dict) -> dict:
            u["comment"] = comment_edit.text()
            u["steam_skin"] = steam_skin_select.currentText()
            return u

        self.submit_button.clicked.connect(lambda: self.save_account(account_name_edit.text(),
                                                                     update_user(user),
                                                                     login_name_selected if not new_account else None))
        close_button.clicked.connect(self.account_dialog_window.close)

        buttons = QHBoxLayout()
        buttons.addWidget(self.submit_button)
        buttons.addWidget(close_button)

        dialog_layout.addLayout(buttons)

        self.account_dialog_window.show()
