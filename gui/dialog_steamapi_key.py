from PySide2.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton

from ._i18n import _


class DialogSteamapiKey:
    steamapi_window: QDialog

    def is_valid_steampi_key(self, key):
        if len(key) == 32:
            return True
        return False

    def steamapi_key_dialog(self):
        self.steamapi_window = QDialog()
        self.steamapi_window.setWindowTitle(_("Set steamapi key"))
        self.steamapi_window.setWindowIcon(self.switcher_logo)

        layout = QVBoxLayout()
        self.steamapi_window.setLayout(layout)

        text_label = QLabel(
            _("Used for getting avatars. Get yours from <a href='https://steamcommunity.com/dev/apikey'>steam</a>"))
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
            self.steamapi_window.hide()
            if self.switcher.first_run:
                self.import_accounts_dialog()

        save_enabled()

        apikey_edit.textChanged.connect(lambda: save_enabled())
        save_button.clicked.connect(lambda: save())

        self.steamapi_window.show()
