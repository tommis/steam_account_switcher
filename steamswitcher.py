#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A GUI program to quickly switch between many steam accounts for ~~Linux~~ (coming) and Windows.
"""
import os
import ntpath
import signal
from PyVDF import PyVDF
import json
import platform
import subprocess
import requests
import time
if platform.system() == "Windows":
  import winreg


class SteamSwitcher:
  steam_dir: str
  changer_path: str
  skins_dir: str
  system_os: str
  #windows_HKCU_registry: winreg
  linux_registry: {}
  settings: dict
  settings_file: str
  steam_skins: []


  def __init__(self):
    self._load_registry()
    self.settings = self._load_settings()
    if self.system_os == "Windows":
      self.skins_dir = ntpath.join(self.steam_dir, "skins")
    else:
      self.skins_dir = os.path.join(self.steam_linux_dir, "skins")
    self.steam_skins = self.get_steam_skins()

  def _load_registry(self):
    self.system_os = platform.system()
    self.steam_dir = (self._get_linux_registry() if self.system_os == "Linux"
                      else self._get_windows_registry() if self.system_os == "Windows" else "ERROR")

  def _get_windows_registry(self) -> dict:
    self.windows_HKCU_registry = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                                "SOFTWARE\\Valve\\Steam", 0, winreg.KEY_ALL_ACCESS)
    return winreg.QueryValueEx(self.windows_HKCU_registry, "SteamPath")[0]

  def _get_linux_registry(self) -> str:
    self.steam_dir = os.path.join(os.path.expanduser("~"), ".steam")
    self.steam_linux_dir = os.path.join(os.path.expanduser("~"), ".local/share/Steam")
    self.registry_path = os.path.join(self.steam_dir, "registry.vdf")
    try:
      self.linux_registry = PyVDF(infile=self.registry_path)
    except Exception as e:
      print("registry load error\n{e}")
    return self.steam_dir

  def _load_settings(self) -> dict:
    self.changer_path = os.getcwd()
    self.settings_file = os.path.join(self.changer_path, "settings.json")
    try:
      with open(self.settings_file, encoding='utf-8') as settings_file:
        return json.load(settings_file)
    except FileNotFoundError:
      print("Settings file not found, creating...")
      self.settings_write(True)
      return self._load_settings()
    except json.JSONDecodeError:
      print("Settings file is corrupted")

  def settings_write(self, new=False):
    empty_settings = {
      "behavior_after_login": "minimize",
      "theme": "dark",
      "display_size": "small",
      "steam_api_key": "",
      "show_avatars": True,
      "use_systemtray": True,
      "users": {}
    }
    try:
      with open(self.settings_file, "w", encoding='utf-8') as settings_file:
        json.dump(empty_settings if new else self.settings, settings_file, indent=2, ensure_ascii=False)
    except FileNotFoundError:
      print("Settings file not found")

  def get_steam_skins(self) -> []:
    l = [ f.name for f in os.scandir(self.skins_dir) if f.is_dir() ]
    l.insert(0, "default")
    return l


  def kill_steam(self):
    if self.system_os == "Linux":
      try:
        with open(os.path.join(self.steam_dir, "steam.pid")) as file:
          pid = file.read()
        os.kill(int(pid), signal.SIGTERM)
      except ProcessLookupError:
        print("Steam isn't running on pid " + pid)
    elif self.system_os == "Windows":
      reg_activeprocess = winreg.OpenKey(self.windows_HKCU_registry, "ACTIVEPROCESS")
      pid = winreg.QueryValueEx(reg_activeprocess, "PID")[0]

      try:
        os.kill(int(pid), signal.SIGTERM)
      except PermissionError:
        print("ERROR: no permission to kill steam on PID {0}".format(pid))
      except OSError:
        print("Steam not running on PID {0}".format(pid))

  def start_steam(self):
    if self.system_os == "Windows":
      steam_exe = winreg.QueryValueEx(self.windows_HKCU_registry, "STEAMEXE")[0]
      subprocess.Popen(steam_exe)
    elif self.system_os == "Linux":
      subprocess.Popen("/usr/bin/steam-runtime")

  def get_steamapi_usersummary(self, uids: list = None) -> dict:
    api_key = self.settings["steam_api_key"]
    if not api_key:
      raise Exception("No steam_api_key defined")
    if not uids:
      uids = [ user.get("steam_uid") for user in self.settings["users"].values() if user.get("steam_uid") != None ]
    api_url = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002"
    response = requests.get(api_url, params={"key": api_key, "steamids": ','.join(uids)})
    if response.status_code == 200 and response.json()["response"]["players"]:
      for steam_user in response.json()["response"]["players"]:
        login_name, user = [ (login_name, user) for (login_name, user) in self.settings["users"].items() if user.get("steam_uid") == steam_user["steamid"] ][0]
        user["steam_user"] = steam_user
        self.settings["users"][login_name] = user
      self.settings_write()
    else:
      return {}


  def set_autologin_account(self, login_name):
    if login_name in self.settings["users"]:
      #self.sync_steam_autologin_accounts()
      user = self.settings["users"][login_name]
      if self.system_os == "Windows":
        try:
          winreg.SetValueEx(self.windows_HKCU_registry, "AutoLoginUser", 0, winreg.REG_SZ, login_name)
          winreg.SetValueEx(self.windows_HKCU_registry, "SkinV5", 0, winreg.REG_SZ, user.get("steam_skin", ""))
        except PermissionError:
          print("ERROR: Insufficient permission to set AutoLoginUser")
      elif self.system_os == "Linux":
        self.linux_registry.edit("Registry.HKCU.Software.Valve.Steam.AutoLoginUser", login_name)
        self.linux_registry.edit("Registry.HKCU.Software.Valve.Steam.SkinV5", user.get("steam_skin", ""))
        self.linux_registry.write_file(self.registry_path)
    else:
        raise ValueError

  def add_account(self, login_name, user, old_login_name = None):
    user = {
      "comment": user.get("comment", ""),
      "display_order": len(self.settings["users"]) + 1,
      "timestamp": user.get("timestamp") if user.get("timestamp") else str(int(time.time())),
      "steam_skin": user.get("steam_skin", ""),
      "steam_user": user.get("steam_user", {})
    }
    if old_login_name:
      self.settings["users"].pop(old_login_name)
      if old_login_name is not login_name:
        try:
          user.pop("steam_user")
          user.pop("steam_name")
        except Exception:
          print("ERROR")


    self.settings["users"][login_name] = user

    print("Saving {0} account".format(login_name))
    self.settings_write()

  def delete_account(self, account_name):
    self.settings["users"].pop(account_name)
    self.settings_write()

  def get_steamuids(self):
    if self.system_os == "Windows":
      loginusers_path = os.path.join(self.steam_dir, "config/loginusers.vdf")
    else:
      loginusers_path = os.path.join(self.steam_linux_dir, "config/loginusers.vdf")
    try:
      loginusers = PyVDF(infile=loginusers_path).getData()["users"]
    except Exception as e:
      print("loginusers.vdf load error\n{0}".format(e))
      return ""

    for uid, user in loginusers.items():
      if not len(uid) == 17 and uid.isnumeric():
        raise Exception("UID: {0} doesn't seem like steam id".format(uid))
      if user["AccountName"] in self.settings["users"]:
        self.settings["users"][user["AccountName"]]["steam_uid"] = uid
        self.settings["users"][user["AccountName"]]["steam_name"] = user["PersonaName"]
    self.settings_write()

  def get_steam_avatars(self, *login_names, **kwargs) -> dict:
    r = {}
    for login_name in login_names[0]:
      if login_name in self.settings["users"]:
        try:
          img_url = self.settings["users"][login_name]["steam_user"].get("avatarfull")
          img_filename = img_url.split("/")[-1] if img_url is not None else "avatar.png"
          avatar_path = os.path.join(self.changer_path, "avatars", img_filename)
          if os.path.isfile(avatar_path):
            r[login_name] = avatar_path
            continue

          response = requests.get(img_url)
          if response.status_code == 200:
            with open(avatar_path, "wb") as img_file:
              img_file.write(response.content)
            r[login_name] = avatar_path
            continue
          else:
            print("Avatar download error")
            r[login_name] = os.path.join(self.changer_path, "avatars/avatar.png")
        except KeyError:
          print("EEROREREQWRJKOJQAWJERKOJAOWEKSRJ")
      else:
        r[login_name] = os.path.join(self.changer_path, "avatars/avatar.png")
    return r

  def sync_steam_autologin_accounts(self):
    loginusers_path = os.path.join(self.steam_dir, "config/loginusers.vdf")
    users = {"users": {}}
    for login_name, user in self.settings["users"].items():
      try:
        users["users"][login_name] = {
          "AccountName": login_name,
          "PersonaName": user["steam_user"].get("personaname", ""),
          "RememberPassword": "1",
          "mostrecent": "0",
          "Timestamp": str(int(time.time())),
          "SkipOfflineModeWarning": "0",
          "WantsOfflineMode": "0"
        }
      except KeyError:
        print("No {0} in settings file".format(login_name))

    # Use with?
    new_vdf = PyVDF()
    new_vdf.setData(users)
    new_vdf.write_file(loginusers_path)


if __name__ == "__main__":
    s = SteamSwitcher()
