from _i18n import _

class Settings:
  def set_show_avatars(self):
    self.switcher.settings["show_avatars"] = not self.switcher.settings.get("show_avatars")
    self.switcher.settings_write()
    self.load_accounts()


  def set_after_login_action(self, item):
    self.switcher.settings["behavior_after_login"] = item.data()
    self.switcher.settings_write()


  def set_size(self, size):
    self.switcher.settings["display_size"] = size
    self.switcher.settings_write()
    self.load_accounts()
