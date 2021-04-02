# Steam account switcher

![Steam account switcher](https://github.com/tommis/steam_account_switcher/workflows/Steam%20account%20switcher/badge.svg?branch=master)

![screenshot](screenshot.png)

A GUI program to quickly switch between many steam accounts for Linux and Windows.

I have found no way to automatically to find out steam profile name and avatar. So for now it has to be a manual menu action.

Your login info is stored in steam installation directory in the files starting with ssfn so this program doesn't actually know your password.

Run with `python main.py`

Remember to get your steamapi key from [steam](https://steamcommunity.com/dev/apikey).

## Features

* Switch between steam account with only few clicks
* No remembering passwords or typing authenticator codes
* Set steam skins per account

## Command line usage

Syntax `python main.py <options>`

Flags  (TODO)

* `-login USERNAME`
* `-add USERNAME` or `-add USERNAME,USERNAME,USERNAME...`z
* `-remove/-delete USERNAME`
* `-list`
* `-about`

#[wiki](https://github.com/tommis/steam_account_switcher/wiki)

## TODO

- [ ] Command line interface
- [X] Linux
- [ ] Code refactoring
- [ ] Actually check something with tests
- [ ] Status bar
- [X] Size menu
- [ ] Make account reordering work
        
## Requirements & installation

- python3+
- pyside2
- pyvdf
- requests
