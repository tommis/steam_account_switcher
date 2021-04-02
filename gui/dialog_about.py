from PySide2.QtWidgets import QDialog, QVBoxLayout, QLabel

from _i18n import _


class DialogAbout:
  def about_dialog(self):
    self.about_dialog = QDialog(self)
    self.about_dialog.setWindowTitle("About")

    layout = QVBoxLayout()
    self.about_dialog.setLayout(layout)

    text_label = QLabel(_("Steam account switcher<br>"
                          "Author: Tommi Saira &lt;tommi@saira.fi&gt;<br>"
                          "Url: <a href='https://github.com/tommis/steam_account_switcher'>github.com/tommis/steam_account_switcher</a>"))

    text_label.setOpenExternalLinks(True)

    layout.addWidget(text_label)

    self.about_dialog.show()
