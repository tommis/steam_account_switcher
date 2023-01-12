from PySide2.QtGui import QStandardItemModel, QStandardItem
from PySide2.QtWidgets import QVBoxLayout, QLabel, QTreeView, QPushButton, QAbstractItemView

from ._i18n import _


class DialogImportAccount():
    def import_accounts_dialog(self):
        self.import_accounts_window.setWindowTitle(_("Import accounts"))
        self.import_accounts_window.setWindowIcon(self.switcher_logo)
        self.import_accounts_window.setMinimumWidth(400)

        layout = QVBoxLayout()
        self.import_accounts_window.setLayout(layout)

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
            # account_row[0].setCheckable(True)
            account_row[2].setEnabled(False)

            if steam_user.get("AccountName") in installed_accounts:
                # account_row = [ x.setEnabled(False) for x in account_row]
                disabled.append(account_row)
            else:
                model.appendRow(account_row)

        # model.appendRows(disabled) #Existing accounts grayed out
        import_accounts_list.resizeColumnToContents(0)

        def import_accounts():
            selected_accounts = import_accounts_list.selectionModel().selectedRows()
            for account in selected_accounts:
                self.switcher.add_account(account.data(0))
            self.steamapi_refresh()
            self.import_accounts_window.hide()

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

        self.import_accounts_window.show()
