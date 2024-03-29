#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A GUI program to quickly switch between many steam accounts for Linux and Windows.
"""
import argparse
import os
import ntpath
import pprint
import signal
import sys

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
    # windows_HKCU_registry: winreg
    linux_registry: {}
    settings: dict
    settings_file: str
    steam_skins: []
    default_avatar: str
    first_run: bool
    stop: bool

    def __init__(self):
        self.first_run = False
        self._load_registry()
        self.settings = self._load_settings()
        if self.system_os == "Windows":
            self.skins_dir = ntpath.join(self.steam_dir, "skins")
        else:
            self.skins_dir = os.path.join(self.steam_linux_dir, "skins")
        self.steam_skins = self.get_steam_skins()
        self.default_avatar = os.path.join(self.changer_path, "avatars/avatar.png")
        self.parser = argparse.ArgumentParser(prog="main.pyw",
                                              usage="%(prog)s [options]",
                                              description="Program to quickly switch between steam accounts.")
        self.args = self.arg_setup()
        self.parse(self.args)

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
            with open(self.settings_file, encoding="utf-8") as settings_file:
                return json.load(settings_file)
        except FileNotFoundError:
            print("Settings file not found, creating...")
            self.first_run = True
            self.settings_write(True)
            return self._load_settings()
        except json.JSONDecodeError:
            print("Settings file is corrupted")

    def settings_write(self, new=False):
        empty_settings = {
            "steam_api_key": "",
            "behavior_after_login": "nothing",
            "theme": "dark",
            "display_size": "medium",
            "show_on_startup": True,
            "show_avatars": True,
            "use_systemtray": True,
            "users": {}
        }
        try:
            with open(self.settings_file, "w", encoding="utf-8") as settings_file:
                json.dump(empty_settings if new else self.settings, settings_file, indent=2, ensure_ascii=False)
        except FileNotFoundError:
            print("Settings file not found")

    def get_steam_skins(self) -> []:
        try:
            l = [f.name for f in os.scandir(self.skins_dir) if f.is_dir()]
            l.insert(0, "default")
            return l
        except FileNotFoundError as e:
            print("Error: is steam installed? \n{0}".format(e))

    def login_with(self, login_name, force=False):
        try:
            if login_name in self.settings["users"] or force:
                self.kill_steam()
                self.set_autologin_account(login_name)
                self.start_steam()
        except Exception as e:
            print("Something went wrong. Are you running as administrator?\n{0}".format(e))
            raise e

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
            except PermissionError as e:
                raise e
            except OSError:
                print("Steam not running on PID {0}".format(pid))

    def start_steam(self):
        if self.system_os == "Windows":
            steam_exe = winreg.QueryValueEx(self.windows_HKCU_registry, "STEAMEXE")[0]
            subprocess.Popen(steam_exe)
        elif self.system_os == "Linux":
            subprocess.Popen("/usr/bin/steam-runtime", stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def arg_setup(self):
        self.parser.add_argument("-l", "--login", type=str, action="store", help="Login with account")
        self.parser.add_argument("-fl", "--force-login", type=str, action="store", help="Login with account, no check")
        self.parser.add_argument("--list", action="store_true", help="List accounts")
        self.parser.add_argument("-a", "--add", type=str, action="store", help="Add account")
        self.parser.add_argument("--delete", "--remove", type=str, action="store", help="Remove account")
        self.parser.add_argument("-s", "--settings", action="store", help="Modify settings")
        self.parser.add_argument("--set", action="store", help="Set settings value to")
        self.parser.add_argument("--first-run", action="store_true", help="Run the first run wizard")

        gui_group = self.parser.add_mutually_exclusive_group(required=False)
        gui_group.add_argument("--gui", action="store_true", help="Show gui")
        gui_group.add_argument("--no-gui", action="store_true", help="Don't show gui")

        tray_group = self.parser.add_mutually_exclusive_group(required=False)
        tray_group.add_argument("--tray", action="store_true", help="Show  systemtray")
        tray_group.add_argument("--no-tray", action="store_true", help="Don't show on systemtray")

        return self.parser.parse_args()

    def parse(self, args):
        pp = pprint.PrettyPrinter(indent=2).pprint
        if args.login and args.login in self.settings["users"]:
            self.login_with(args.login)
        elif args.force_login:
            self.login_with(args.force_login, force=True)
        elif args.login and args.login not in self.settings["users"]:
            print("Login user not in settings file, ignoring...\nUse --force-login {0} instead".format(args.login))

        if args.list:
            pp(self.settings.get("users", "No installed users").keys())
            self.stop = True

        if args.delete:
            if args.delete in self.settings["users"]:
                self.delete_account(args.delete)
            else:
                print("User {0} not in settings file".format(args.delete))

    def get_steamapi_usersummary(self, uids: list = None, get_missing=False):
        api_key = self.settings["steam_api_key"]
        if not api_key:
            raise Exception("No steam_api_key defined")
        if not uids:
            if get_missing:
                uids = [user.get("steam_uid") for user in self.settings["users"].values() if not user.get("steam_user")]
            else:
                uids = [user.get("steam_uid") for user in self.settings["users"].values()]
        self.settings["last_refreshed"] = str(int(time.time()))
        api_url = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002"
        response = requests.get(api_url, params={"key": api_key, "steamids": ",".join(uids)})
        if response.status_code == 200 and response.json()["response"]["players"]:
            for steam_user in response.json()["response"]["players"]:
                login_name, user = [(login_name, user) for (login_name, user) in self.settings["users"].items() if
                                    user.get("steam_uid") == steam_user["steamid"]][0]
                user["steam_user"] = steam_user
                user["steam_name"] = steam_user.get("personaname")
                self.settings["users"][login_name] = user
            self.settings_write()
        else:
            raise Exception("ERROR: downloading usersummaries")

    def set_autologin_account(self, login_name):
        user = self.settings["users"].get(login_name)
        if self.system_os == "Windows":
            try:
                winreg.SetValueEx(self.windows_HKCU_registry, "AutoLoginUser", 0, winreg.REG_SZ, login_name)
                if user:
                    winreg.SetValueEx(self.windows_HKCU_registry, "SkinV5", 0, winreg.REG_SZ,
                                      user.get("steam_skin", ""))
            except PermissionError:
                print("ERROR: Insufficient permission to set AutoLoginUser")
        elif self.system_os == "Linux":
            self.linux_registry.edit("Registry.HKCU.Software.Valve.Steam.AutoLoginUser", login_name)
            if user:
                self.linux_registry.edit("Registry.HKCU.Software.Valve.Steam.SkinV5", user.get("steam_skin", ""))
            self.linux_registry.write_file(self.registry_path)

    def set_account_localconfig(self, uid):
        def convert_uid(uid: str) -> str:
            return "asd"

        localconfig_path = os.path.join(self.steam_dir, "userdata", convert_uid(uid), "localconfig.vdf")

        print(localconfig_path)

    def add_account(self, login_name, user=None, original_login_name=None):
        if not user:
            user = {}
        skin = user.get("steam_skin")
        user = {
            "comment": user.get("comment", ""),
            "display_order": len(self.settings["users"].keys()) + 1,
            "timestamp": user.get("timestamp") if user.get("timestamp") else str(int(time.time())),
            "steam_skin": skin if skin in self.steam_skins else "default",
            "steam_uid": user.get("steam_uid", ""),
            "steam_user": user.get("steam_user", {})
        }
        if original_login_name and login_name != original_login_name:
            try:
                user.pop("steam_user")
                user.pop("steam_name")
            except KeyError:
                pass
            self.settings["users"].pop(original_login_name)

        self.settings["users"][login_name] = user
        self.set_account_localconfig(user["steam_uid"])

        print("Saving {0} account".format(login_name))
        self.settings_write()

    def delete_account(self, account_name):
        self.settings["users"].pop(account_name)
        self.settings_write()

    def load_loginusers(self) -> dict:
        if self.system_os == "Windows":
            loginusers_path = os.path.join(self.steam_dir, "config/loginusers.vdf")
        else:
            loginusers_path = os.path.join(self.steam_linux_dir, "config/loginusers.vdf")
        try:
            with open(loginusers_path, encoding="utf-8") as loginusers_file:
                return PyVDF(infile=loginusers_file).getData()["users"]
        except Exception as e:
            print("loginusers.vdf load error\n{0}".format(e))

    def update_steamuids(self, no_save=False):
        loginusers = self.load_loginusers()

        for uid, user in loginusers.items():
            if not len(uid) == 17 and uid.isnumeric():
                raise Exception("UID: {0} doesn't seem like steam id".format(uid))
            if user["AccountName"] in self.settings["users"] and not no_save:
                self.settings["users"][user["AccountName"]]["steam_uid"] = uid
                self.settings["users"][user["AccountName"]]["steam_name"] = user["PersonaName"]
        if not no_save:
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
                        r[login_name] = self.default_avatar
                except KeyError:
                    print("EEROREREQWRJKOJQAWJERKOJAOWEKSRJ")
            else:
                r[login_name] = self.default_avatar
        return r


if __name__ == "__main__":
    steam_switcher = SteamSwitcher()
    if not len(sys.argv) > 1:
        steam_switcher.parser.print_help()
