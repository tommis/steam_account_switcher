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
  changer_settings: dict
  changer_settings_file: str


  def __init__(self):
    self._load_registry()
    self.changer_settings = self._load_settings()
    if self.system_os == "Windows":
      self.skins_dir = ntpath.join(self.steam_dir, "skins")
    else:
      self.skins_dir = os.path.join(self.steam_linux_dir, "skins")

  def _load_registry(self):
    self.system_os = platform.system()
    self.steam_dir = (self._get_linux_registry() if self.system_os == "Linux"
                      else self._get_windows_registry() if self.system_os == "Windows" else "ERROR")

  def _get_windows_registry(self) -> str:
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
      print("registry load error")
    return self.steam_dir

  def _load_settings(self) -> dict:
    self.changer_path = os.getcwd()
    self.changer_settings_file = os.path.join(self.changer_path, "changer.json")
    try:
      with open(self.changer_settings_file, encoding='utf-8') as settings_file:
        return json.load(settings_file)
    except FileNotFoundError:
      print("Settings file not found, creating...")
      empty_settings = {
        "behavior_after_login": "minimize",
        "theme": "dark",
        "steam_api_key": "",
        "users": {}
      }
      with open(self.changer_settings_file, 'w+', encoding='utf-8') as settings_file:
        json.dump(empty_settings, settings_file, indent=2, ensure_ascii=False)
      return self._load_settings()
    except json.JSONDecodeError:
      print("Settings file is corrupted")

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

  def get_steamapi_usersummary(self, uid: str) -> str:
    api_key = self.changer_settings["steam_api_key"]
    api_url = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002"
    response_json = requests.get(api_url, params={"key": api_key, "steamids": uid}).json()
    return response_json["response"]["players"][0]


  def set_autologin_account(self, login_name):
    if login_name in self.changer_settings["users"]:
      #self.sync_steam_autologin_accounts()
      user = self.changer_settings["users"][login_name]
      if self.system_os == "Windows":
        try:
          winreg.SetValueEx(self.windows_HKCU_registry, "AutoLoginUser", 0, winreg.REG_SZ, login_name)
          winreg.SetValueEx(self.windows_HKCU_registry, "SkinV5", 0, winreg.REG_SZ, "" if user["steam_skin"] == "default" else user["steam_skin"])
        except PermissionError:
          print("ERROR: Insufficient permission to set AutoLoginUser")
      elif self.system_os == "Linux":
        self.linux_registry.edit("Registry.HKCU.Software.Valve.Steam.AutoLoginUser", login_name)
        self.linux_registry.edit("Registry.HKCU.Software.Valve.Steam.SkinV5", "" if user["steam_skin"] == "default" else user["steam_skin"])
        self.linux_registry.write_file(self.registry_path)
    else:
        raise ValueError

  def add_new_account(self, account_name, old_account_name="", comment="", steam_skin="default", display_order=0):
    user = {
      "comment": comment,
      "display_order": len(self.changer_settings["users"]) + 1,
      "timestamp": str(time.time()),
      "steam_skin": steam_skin,
      "steam_user": {} #self.get_steamapi_usersummary(uid) if uid != "" else {}
    }
    if old_account_name != "":
      self.changer_settings["users"].pop(old_account_name)

    self.changer_settings["users"][account_name] = user

    print("Saving {0} account".format(account_name))
    with open(self.changer_settings_file, 'w', encoding='utf-8') as settings_file:
      json.dump(self.changer_settings, settings_file, indent=2, ensure_ascii=False)

    self.get_steamids()

  def delete_account(self, account_name):
    self.changer_settings["users"].pop(account_name)
    with open(self.changer_settings_file, 'w', encoding='utf-8') as settings_file:
      json.dump(self.changer_settings, settings_file, indent=2, ensure_ascii=False)

  def get_steamids(self):
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
      if user["AccountName"] in self.changer_settings["users"]:
        self.changer_settings["users"][user["AccountName"]]["steam_user"] = self.get_steamapi_usersummary(uid)

    try:
      with open(self.changer_settings_file, "w", encoding='utf-8') as settings_file:
        json.dump(self.changer_settings, settings_file, indent=2, ensure_ascii=False)
    except FileNotFoundError:
      print("Settings file not found")

  def get_steam_avatars(self, *login_names, **kwargs) -> dict:
    r = {}
    for login_name in login_names[0]:
      if login_name in self.changer_settings["users"]:
        try:
          img_url = self.changer_settings["users"][login_name]["steam_user"].get("avatarfull")
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
    for login_name, user in self.changer_settings["users"].items():
      try:
        users["users"][login_name] = {
          "AccountName": login_name,
          "PersonaName": user["steam_user"]["personaname"],
          "RememberPassword": "1",
          "mostrecent": "0",
          "Timestamp": str(time.time()),
          "SkipOfflineModeWarning": "0",
          "WantsOfflineMode": "0"
        }
      except KeyError:
        print("No {0} in settings file".format(login_name))

    # Use with?
    new_vdf = PyVDF()
    new_vdf.setData(users)
    new_vdf.write_file(loginusers_path)


  def get_steam_skins(self) -> []:
    l = [ f.name for f in os.scandir(self.skins_dir) if f.is_dir() ]
    l.insert(0, "default")
    return l

if __name__ == "__main__":
    s = SteamSwitcher()

    #print(s.get_steam_avatars(*["tommisas", "tommisa"]))
    print(s.get_steam_avatars("sukamanblyat", "pentti_makipetaja_mahonen"))

    #s.add_new_account("tommi")

    #s.get_steamids()
    #s.set_autologin_account("tommisa")

    #s.sync_steam_autologin_accounts()

    #s.kill_steam()
    #s.start_steam()
