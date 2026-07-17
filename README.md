
# 🎮 RenPG Maker

![RenPG Maker Logo](img/logo_512.png)

![Python](https://img.shields.io/badge/python-3.8+-06b6d4.svg)
![Platforms](https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-7c3aed.svg)
[![README Italiano](https://img.shields.io/badge/README-Italiano-009246.svg)](README_IT.md)

Convert **RPG Maker MV/MZ** games into **Ren'Py** visual novels, keeping only dialogues, choices, images, audio, variables and conditional branches.

![RenPG Maker GUI](img/gui.png)

## 🚀 Installation & Launch

```bash
# macOS / Linux
./start.sh

# Windows
start.bat
```

`uv` is installed automatically if missing. The `start.sh` / `start.bat` scripts also create a virtual environment and install the required dependencies.

You can also run the GUI directly:

```bash
python3 -m rpgm2vn.gui
```

Or use the command-line interface:

```bash
python3 -m rpgm2vn.cli /path/to/game/www/data /path/to/output
```

## 🎬 Convert & Build

The GUI also supports a one-click **Convert & Build** workflow:

1. Select the game and output folder.
2. Choose the build target: `all`, `win`, `mac` or `linux`.
3. Click **Convert & Build**.

The first time you build, Ren'Py SDK 8.5.3 is downloaded automatically into `renpy-sdk/`. After that, the project is converted and packaged for the selected desktop platform.

Encrypted RPG Maker MV/MZ assets (`.rpgmvp`, `.rpgmvo`, `.rpgmvm`, `.rpgmve`) are decrypted automatically using the key from `System.json`. Movies from the `movies/` folder are also copied into the project.

## 🎨 UI, icon and splash screen

The GUI uses a color palette inspired by the project logo, with the logo displayed at the top-left and the RenPG icon in the window title. The generated Ren'Py game also shows a splash screen before the main menu, using `img/splash.png`, displayed once per session for 2.5 seconds.

## 🍎 macOS .app bundle

On macOS you can build a clickable `.app` bundle:

```bash
./build_mac_app.sh
```

This creates a self-contained `dist/RenPGMaker.app` with the proper icon, embedded virtual environment and project files. It runs natively on Apple Silicon (M1/M2/M3) as well as Intel Macs.
