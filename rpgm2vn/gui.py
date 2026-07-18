"""Interfaccia grafica per RenPG Maker basata su customtkinter."""

import json
import re
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk
from PIL import Image, ImageTk

from .generator import RenpyProjectGenerator
from . import sdk_manager


# Palette estratta dal logo
COLOR_DARK = "#1a1210"
COLOR_PRIMARY = "#3c3030"
COLOR_SECONDARY = "#2c2020"
COLOR_ACCENT = "#5c483c"
COLOR_TEXT = "#e8ddd2"
COLOR_HIGHLIGHT = "#fc9c00"
COLOR_HOVER = "#e88a2a"
COLOR_ORANGE = "#fc9c00"
COLOR_ORANGE_HOVER = "#e88a2a"
COLOR_TEAL = "#8d7356"

LOGO_PATH = Path(__file__).resolve().parent.parent / "img" / "logo_256.png"
ICON_PATH = Path(__file__).resolve().parent.parent / "img" / "icon.iconset" / "icon_256x256.png"
CONFIG_PATH = Path.home() / ".renpgmaker.json"


TEXTS = {
    "en": {
        "game": "Game",
        "output": "Output",
        "output_ph": "Base output folder",
        "app_btn": ".app",
        "folder_btn": "Folder",
        "browse_btn": "Browse",
        "advanced": "⚙️ Advanced options",
        "start_map": "Start Map",
        "start_map_ph": "auto",
        "include_events": "Include Events",
        "include_events_ph": "e.g. 1, 2, 3",
        "no_prefix": "No dialogue prefix",
        "convert": "▶  Convert & Build",
        "cancel": "Cancel",
        "ready": "Ready",
        "converting": "Converting, please wait...",
        "conversion_done": "Conversion done.",
        "build_failed": "Build failed",
        "select_game": "Please select a game.",
        "select_output": "Please select an output folder.",
        "game_not_found": "Game path not found:\n{}",
        "data_not_found": "Could not find RPG Maker data folder in:\n{}\n\nExpected a 'www/data' folder or a macOS .app bundle.",
        "start_map_error": "Start Map must be a number.",
        "events_error": "Include Events must be numbers separated by spaces or commas.",
        "success_title": "Done",
        "success_msg": "Ren'Py project generated in:\n{}",
        "build_success": "Build completed:\n{}",
        "error": "Error",
        "select_app": "Select .app bundle",
        "select_folder": "Select game folder",
        "select_output_folder": "Select output folder",
        "tooltip_start_map": "ID of the starting map. Leave empty to use System.json.",
        "tooltip_include_events": "Comma or space separated list of event IDs to include. Leave empty for all.",
        "tooltip_no_prefix": "Disable extraction of the speaker name from variable prefixes.",
        "language": "Language",
        "sdk_section": "🎬 Ren'Py SDK",
        "sdk_path": "SDK path",
        "sdk_download": "Download SDK",
        "sdk_update": "Update SDK",
        "sdk_ready": "SDK is ready.",
        "sdk_downloading": "Downloading Ren'Py SDK...",
        "sdk_extracting": "Extracting Ren'Py SDK...",
        "build_target": "Build target",
        "build_target_all": "All desktop",
        "build_target_win": "Windows",
        "build_target_mac": "macOS",
        "build_target_linux": "Linux",
        "building": "Building...",
    },
    "it": {
        "game": "Gioco",
        "output": "Output",
        "output_ph": "Cartella base di output",
        "app_btn": ".app",
        "folder_btn": "Cartella",
        "browse_btn": "Sfoglia",
        "advanced": "⚙️ Opzioni avanzate",
        "start_map": "Mappa iniziale",
        "start_map_ph": "auto",
        "include_events": "Includi eventi",
        "include_events_ph": "es. 1, 2, 3",
        "no_prefix": "Nessun prefisso dialogo",
        "convert": "▶ Converti e Builda",
        "cancel": "Annulla",
        "ready": "Pronto",
        "converting": "Conversione in corso...",
        "conversion_done": "Conversione completata.",
        "build_failed": "Build fallita",
        "select_game": "Seleziona un gioco.",
        "select_output": "Seleziona una cartella di output.",
        "game_not_found": "Percorso gioco non trovato:\n{}",
        "data_not_found": "Cartella dati RPG Maker non trovata in:\n{}\n\nAtteso 'www/data' o un bundle .app macOS.",
        "start_map_error": "Mappa iniziale deve essere un numero.",
        "events_error": "Includi eventi deve contenere numeri separati da spazi o virgole.",
        "success_title": "Fatto",
        "success_msg": "Progetto Ren'Py generato in:\n{}",
        "build_success": "Build completata:\n{}",
        "error": "Errore",
        "select_app": "Seleziona bundle .app",
        "select_folder": "Seleziona cartella gioco",
        "select_output_folder": "Seleziona cartella output",
        "tooltip_start_map": "ID della mappa iniziale. Lascia vuoto per usare System.json.",
        "tooltip_include_events": "Elenco di ID eventi separati da virgola o spazio. Lascia vuoto per tutti.",
        "tooltip_no_prefix": "Disabilita l'estrazione del nome del personaggio dai prefissi delle variabili.",
        "language": "Lingua",
        "sdk_section": "🎬 Ren'Py SDK",
        "sdk_path": "Percorso SDK",
        "sdk_download": "Scarica SDK",
        "sdk_update": "Aggiorna SDK",
        "sdk_ready": "SDK pronto.",
        "sdk_downloading": "Download SDK Ren'Py...",
        "sdk_extracting": "Estrazione SDK Ren'Py...",
        "build_target": "Target build",
        "build_target_all": "Tutti i desktop",
        "build_target_win": "Windows",
        "build_target_mac": "macOS",
        "build_target_linux": "Linux",
        "building": "Build in corso...",
    },
    "es": {
        "game": "Juego",
        "output": "Salida",
        "output_ph": "Carpeta base de salida",
        "app_btn": ".app",
        "folder_btn": "Carpeta",
        "browse_btn": "Examinar",
        "advanced": "⚙️ Opciones avanzadas",
        "start_map": "Mapa inicial",
        "start_map_ph": "auto",
        "include_events": "Incluir eventos",
        "include_events_ph": "ej. 1, 2, 3",
        "no_prefix": "Sin prefijo de diálogo",
        "convert": "▶ Convertir y compilar",
        "cancel": "Cancelar",
        "ready": "Listo",
        "converting": "Convirtiendo, espera...",
        "conversion_done": "Conversión completada.",
        "build_failed": "Compilación fallida",
        "select_game": "Selecciona un juego.",
        "select_output": "Selecciona una carpeta de salida.",
        "game_not_found": "Ruta del juego no encontrada:\n{}",
        "data_not_found": "No se encontró la carpeta de datos en:\n{}\n\nSe esperaba 'www/data' o un bundle .app de macOS.",
        "start_map_error": "Mapa inicial debe ser un número.",
        "events_error": "Incluir eventos debe ser números separados por espacios o comas.",
        "success_title": "Hecho",
        "success_msg": "Proyecto Ren'Py generado en:\n{}",
        "build_success": "Compilación completada:\n{}",
        "error": "Error",
        "select_app": "Seleccionar bundle .app",
        "select_folder": "Seleccionar carpeta del juego",
        "select_output_folder": "Seleccionar carpeta de salida",
        "tooltip_start_map": "ID del mapa inicial. Dejar vacío para usar System.json.",
        "tooltip_include_events": "Lista de IDs de eventos separados por coma o espacio. Dejar vacío para todos.",
        "tooltip_no_prefix": "Desactiva la extracción del nombre del personaje desde prefijos de variables.",
        "language": "Idioma",
        "sdk_section": "🎬 Ren'Py SDK",
        "sdk_path": "Ruta SDK",
        "sdk_download": "Descargar SDK",
        "sdk_update": "Actualizar SDK",
        "sdk_ready": "SDK listo.",
        "sdk_downloading": "Descargando SDK Ren'Py...",
        "sdk_extracting": "Extrayendo SDK Ren'Py...",
        "build_target": "Target de compilación",
        "build_target_all": "Todos los escritorios",
        "build_target_win": "Windows",
        "build_target_mac": "macOS",
        "build_target_linux": "Linux",
        "building": "Compilando...",
    },
}


class Tooltip:
    """Tooltip semplice che appare al passaggio del mouse."""

    def __init__(self, widget: tk.Widget, text: str):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        self.id = None
        self.widget.bind("<Enter>", self._enter)
        self.widget.bind("<Leave>", self._leave)

    def set_text(self, text: str):
        self.text = text

    def _enter(self, _event=None):
        self._schedule()

    def _leave(self, _event=None):
        self._unschedule()
        self._hide()

    def _schedule(self):
        self.id = self.widget.after(500, self._show)

    def _unschedule(self):
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None

    def _show(self):
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        self.tipwindow = tk.Toplevel(self.widget)
        self.tipwindow.wm_overrideredirect(True)
        self.tipwindow.wm_geometry(f"+{x}+{y}")
        tk.Label(
            self.tipwindow,
            text=self.text,
            background=COLOR_DARK,
            foreground=COLOR_TEXT,
            justify="left",
            wraplength=280,
            padx=8,
            pady=6,
            font=("SF Pro", 10),
        ).pack()

    def _hide(self):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None


def find_data_dir(game_path: Path) -> Path | None:
    """Cerca la cartella dati www/data a partire dal percorso gioco.

    Su macOS il percorso può essere un bundle .app contenente
    Contents/Resources/app.nw oppure una cartella con www/data.
    """
    game_path = game_path.resolve()
    candidates = [game_path / "www" / "data", game_path / "data", game_path]
    if game_path.suffix.lower() == ".app":
        bundle = game_path / "Contents" / "Resources" / "app.nw"
        candidates = [
            bundle / "www" / "data",
            bundle / "data",
            bundle,
            *candidates,
        ]

    for candidate in candidates:
        if candidate.is_dir() and (
            (candidate / "System.json").is_file()
            or any(candidate.glob("Map*.json"))
        ):
            return candidate
    return None


class RenPGMakerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("RenPG Maker")
        self.geometry("920x720")
        self.minsize(820, 620)
        self.configure(fg_color=COLOR_DARK)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.is_mac = sys.platform == "darwin"
        self._locale = "it"
        self._text_refs: dict[str, object] = {}
        self._tooltips: list[Tooltip] = []
        self._set_icon_and_logo()
        self._build_ui()
        self._update_texts()
        self._load_settings()

    def _set_icon_and_logo(self):
        self._icon_ref = None
        self._logo_image = None
        icon_path = ICON_PATH if ICON_PATH.exists() else LOGO_PATH
        if not icon_path.exists():
            return
        try:
            self._icon_ref = ImageTk.PhotoImage(file=str(icon_path))
            self.wm_iconphoto(False, self._icon_ref)
        except Exception:
            pass

    def _t(self, key: str) -> str:
        return TEXTS[self._locale].get(key, key)

    def _set_language(self, display_name: str):
        mapping = {"Italiano": "it", "English": "en", "Español": "es"}
        code = mapping.get(display_name, "en")
        self._locale = code
        self._update_texts()

    def _set_status(self, text: str):
        self.status_label.configure(text=text)

    def _update_texts(self):
        for key, widget in self._text_refs.items():
            text = self._t(key)
            if key.endswith("_ph"):
                widget.configure(placeholder_text=text)
            elif key == "sdk_download":
                sdk_key = "sdk_update" if sdk_manager.is_sdk_present() else "sdk_download"
                widget.configure(text=self._t(sdk_key))
            else:
                widget.configure(text=text)
        for tip in self._tooltips:
            tip.set_text(self._t(tip._key))
        self.status_label.configure(text=self._t("ready"))

    # ─── UI Build ────────────────────────────────────────────────────────

    def _build_ui(self):
        pad = {"padx": 14, "pady": 8}

        # Titolo
        header = ctk.CTkFrame(
            self,
            fg_color=COLOR_PRIMARY,
            corner_radius=12,
            border_width=2,
            border_color=COLOR_ACCENT,
        )
        header.pack(fill="x", **pad)
        if LOGO_PATH.exists():
            try:
                self._logo_image = ctk.CTkImage(
                    Image.open(LOGO_PATH),
                    size=(64, 64),
                )
                ctk.CTkLabel(header, image=self._logo_image, text="").pack(
                    side="left", padx=(10, 8), pady=8
                )
            except Exception:
                pass
        ctk.CTkLabel(
            header,
            text="RenPG Maker",
            text_color=COLOR_TEXT,
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(side="left")

        # Lingua
        lang_frame = ctk.CTkFrame(header, fg_color="transparent")
        lang_frame.pack(side="right", padx=10)
        self._text_refs["language"] = ctk.CTkLabel(
            lang_frame, text="", text_color=COLOR_TEXT
        )
        self._text_refs["language"].pack(side="left", padx=(0, 6))
        self._lang_var = ctk.StringVar(value="Italiano")
        self._lang_menu = ctk.CTkOptionMenu(
            lang_frame,
            variable=self._lang_var,
            values=["Italiano", "English", "Español"],
            command=self._set_language,
            fg_color=COLOR_SECONDARY,
            button_color=COLOR_TEAL,
            button_hover_color=COLOR_HIGHLIGHT,
            dropdown_fg_color=COLOR_PRIMARY,
            dropdown_hover_color=COLOR_SECONDARY,
            text_color=COLOR_TEXT,
            width=120,
        )
        self._lang_menu.pack(side="left")

        # Selezione gioco
        game_frame = ctk.CTkFrame(
            self,
            fg_color=COLOR_SECONDARY,
            corner_radius=12,
            border_width=2,
            border_color=COLOR_ACCENT,
        )
        game_frame.pack(fill="x", padx=14, pady=(4, 4))

        self._text_refs["game"] = ctk.CTkLabel(
            game_frame, text="", text_color=COLOR_TEXT, width=80, anchor="w"
        )
        self._text_refs["game"].pack(side="left", padx=(12, 6), pady=12)

        self.game_entry = ctk.CTkEntry(
            game_frame,
            placeholder_text="",
            fg_color=COLOR_DARK,
            border_color=COLOR_ACCENT,
            text_color=COLOR_TEXT,
        )
        self._text_refs["game_ph"] = self.game_entry
        self.game_entry.pack(side="left", fill="x", expand=True, padx=(0, 6), pady=12)

        if self.is_mac:
            self._text_refs["app_btn"] = ctk.CTkButton(
                game_frame,
                text="",
                width=60,
                fg_color=COLOR_SECONDARY,
                hover_color=COLOR_HOVER,
                border_width=1,
                border_color=COLOR_ACCENT,
                corner_radius=8,
                command=self._pick_app,
            )
            self._text_refs["app_btn"].pack(side="left", padx=(0, 4), pady=12)

        self._text_refs["folder_btn"] = ctk.CTkButton(
            game_frame,
            text="",
            width=80,
            fg_color=COLOR_SECONDARY,
            hover_color=COLOR_HOVER,
            border_width=1,
            border_color=COLOR_ACCENT,
            corner_radius=8,
            command=self._pick_folder,
        )
        self._text_refs["folder_btn"].pack(side="left", padx=(0, 12), pady=12)

        # Selezione output
        out_frame = ctk.CTkFrame(
            self,
            fg_color=COLOR_PRIMARY,
            corner_radius=12,
            border_width=2,
            border_color=COLOR_ACCENT,
        )
        out_frame.pack(fill="x", padx=14, pady=(4, 4))

        self._text_refs["output"] = ctk.CTkLabel(
            out_frame, text="", text_color=COLOR_TEXT, width=80, anchor="w"
        )
        self._text_refs["output"].pack(side="left", padx=(12, 6), pady=12)

        self.output_entry = ctk.CTkEntry(
            out_frame,
            placeholder_text="",
            fg_color=COLOR_DARK,
            border_color=COLOR_ACCENT,
            text_color=COLOR_TEXT,
        )
        self._text_refs["output_ph"] = self.output_entry
        self.output_entry.pack(side="left", fill="x", expand=True, padx=(0, 6), pady=12)

        self._text_refs["browse_btn"] = ctk.CTkButton(
            out_frame,
            text="",
            width=80,
            fg_color=COLOR_SECONDARY,
            hover_color=COLOR_HOVER,
            border_width=1,
            border_color=COLOR_ACCENT,
            corner_radius=8,
            command=self._pick_output,
        )
        self._text_refs["browse_btn"].pack(side="left", padx=(0, 12), pady=12)

        # SDK Ren'Py
        sdk_frame = ctk.CTkFrame(
            self,
            fg_color=COLOR_TEAL,
            corner_radius=12,
            border_width=2,
            border_color=COLOR_ACCENT,
        )
        sdk_frame.pack(fill="x", padx=14, pady=(4, 4))

        self._text_refs["sdk_section"] = ctk.CTkLabel(
            sdk_frame,
            text="",
            text_color=COLOR_TEXT,
            font=ctk.CTkFont(weight="bold"),
        )
        self._text_refs["sdk_section"].pack(anchor="w", padx=12, pady=(10, 4))

        sdk_row = ctk.CTkFrame(sdk_frame, fg_color="transparent")
        sdk_row.pack(fill="x", padx=12, pady=(4, 10))

        self._text_refs["sdk_path"] = ctk.CTkLabel(
            sdk_row, text="", text_color=COLOR_TEXT, width=80, anchor="w"
        )
        self._text_refs["sdk_path"].pack(side="left", padx=(0, 6))

        self.sdk_path_label = ctk.CTkLabel(
            sdk_row,
            text=str(sdk_manager.sdk_dir()),
            text_color=COLOR_TEXT,
            anchor="w",
        )
        self.sdk_path_label.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self._text_refs["sdk_download"] = ctk.CTkButton(
            sdk_row,
            text="",
            width=140,
            fg_color=COLOR_SECONDARY,
            hover_color=COLOR_HOVER,
            border_width=1,
            border_color=COLOR_ACCENT,
            corner_radius=8,
            command=self._download_sdk,
        )
        self._text_refs["sdk_download"].pack(side="left")

        # Opzioni avanzate
        adv_frame = ctk.CTkFrame(
            self,
            fg_color=COLOR_SECONDARY,
            corner_radius=12,
            border_width=2,
            border_color=COLOR_ACCENT,
        )
        adv_frame.pack(fill="x", padx=14, pady=(4, 4))

        self._text_refs["advanced"] = ctk.CTkLabel(
            adv_frame,
            text="",
            text_color=COLOR_TEXT,
            font=ctk.CTkFont(weight="bold"),
        )
        self._text_refs["advanced"].pack(anchor="w", padx=12, pady=(10, 4))

        opts = ctk.CTkFrame(adv_frame, fg_color="transparent")
        opts.pack(fill="x", padx=12, pady=(4, 10))

        self._text_refs["start_map"] = ctk.CTkLabel(
            opts, text="", text_color=COLOR_TEXT
        )
        self._text_refs["start_map"].grid(
            row=0, column=0, sticky="w", padx=(0, 8), pady=4
        )
        self.start_map_entry = ctk.CTkEntry(
            opts,
            width=100,
            placeholder_text="",
            fg_color=COLOR_DARK,
            border_color=COLOR_ACCENT,
            text_color=COLOR_TEXT,
        )
        self._text_refs["start_map_ph"] = self.start_map_entry
        self.start_map_entry.grid(row=0, column=1, sticky="w", pady=4)

        self._text_refs["include_events"] = ctk.CTkLabel(
            opts, text="", text_color=COLOR_TEXT
        )
        self._text_refs["include_events"].grid(
            row=1, column=0, sticky="w", padx=(0, 8), pady=4
        )
        self.include_events_entry = ctk.CTkEntry(
            opts,
            width=200,
            placeholder_text="",
            fg_color=COLOR_DARK,
            border_color=COLOR_ACCENT,
            text_color=COLOR_TEXT,
        )
        self._text_refs["include_events_ph"] = self.include_events_entry
        self.include_events_entry.grid(row=1, column=1, sticky="w", pady=4)

        self.no_prefix_var = tk.IntVar(value=0)
        self._text_refs["no_prefix"] = ctk.CTkSwitch(
            opts,
            text="",
            text_color=COLOR_TEXT,
            variable=self.no_prefix_var,
            onvalue=1,
            offvalue=0,
            progress_color=COLOR_TEAL,
        )
        self._text_refs["no_prefix"].grid(
            row=2, column=0, columnspan=2, sticky="w", pady=4
        )

        # Tooltip
        self._tooltip_targets = [
            (self._text_refs["start_map"], "tooltip_start_map"),
            (self.start_map_entry, "tooltip_start_map"),
            (self._text_refs["include_events"], "tooltip_include_events"),
            (self.include_events_entry, "tooltip_include_events"),
            (self._text_refs["no_prefix"], "tooltip_no_prefix"),
        ]
        for widget, key in self._tooltip_targets:
            tip = Tooltip(widget, "")
            tip._key = key
            self._tooltips.append(tip)

        # Target build
        target_frame = ctk.CTkFrame(
            self,
            fg_color=COLOR_PRIMARY,
            corner_radius=12,
            border_width=2,
            border_color=COLOR_ACCENT,
        )
        target_frame.pack(fill="x", padx=14, pady=(4, 4))

        self._text_refs["build_target"] = ctk.CTkLabel(
            target_frame, text="", text_color=COLOR_TEXT, width=100, anchor="w"
        )
        self._text_refs["build_target"].pack(side="left", padx=(12, 6), pady=12)

        self._build_target_var = ctk.StringVar(value="all")
        self._build_target_menu = ctk.CTkOptionMenu(
            target_frame,
            variable=self._build_target_var,
            values=["all", "win", "mac", "linux"],
            fg_color=COLOR_SECONDARY,
            button_color=COLOR_TEAL,
            button_hover_color=COLOR_HIGHLIGHT,
            dropdown_fg_color=COLOR_PRIMARY,
            dropdown_hover_color=COLOR_SECONDARY,
            text_color=COLOR_TEXT,
            width=140,
        )
        self._build_target_menu.pack(side="left", padx=(0, 12), pady=12)

        # Azione
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.pack(fill="x", padx=14, pady=(8, 4))

        self._text_refs["convert"] = ctk.CTkButton(
            action_frame,
            text="",
            font=ctk.CTkFont(size=14, weight="bold"),
            width=220,
            height=40,
            fg_color=COLOR_ORANGE,
            hover_color=COLOR_ORANGE_HOVER,
            text_color="white",
            corner_radius=10,
            command=self._convert,
        )
        self._text_refs["convert"].pack(side="left")

        self._text_refs["cancel"] = ctk.CTkButton(
            action_frame,
            text="",
            font=ctk.CTkFont(size=12, weight="bold"),
            width=100,
            height=40,
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_HOVER,
            text_color="white",
            corner_radius=10,
            command=self._cancel,
            state="disabled",
        )
        self._text_refs["cancel"].pack(side="left", padx=(8, 0))

        self.progress = ctk.CTkProgressBar(
            action_frame,
            mode="indeterminate",
            width=200,
            progress_color=COLOR_TEAL,
        )
        self.progress.pack(side="left", fill="x", expand=True, padx=(12, 0), pady=8)
        self.progress.set(0)

        # Log
        self.log_textbox = ctk.CTkTextbox(
            self,
            height=120,
            fg_color=COLOR_DARK,
            text_color=COLOR_TEXT,
            border_color=COLOR_ACCENT,
            border_width=1,
            state="disabled",
        )
        self.log_textbox.pack(fill="x", padx=14, pady=(4, 4))

        # Stato
        self.status_label = ctk.CTkLabel(
            self,
            text="",
            text_color=COLOR_TEXT,
            font=ctk.CTkFont(size=12),
            anchor="w",
        )
        self.status_label.pack(fill="x", padx=14, pady=(0, 8))

    # ─── Actions ─────────────────────────────────────────────────────────

    def _pick_app(self):
        initialdir = str(Path.home() / "Downloads")
        path = filedialog.askopenfilename(
            title=self._t("select_app"), initialdir=initialdir
        )
        if path:
            self.game_entry.delete(0, ctk.END)
            self.game_entry.insert(0, path)

    def _pick_folder(self):
        initialdir = str(Path.home() / "Downloads")
        path = filedialog.askdirectory(
            title=self._t("select_folder"), initialdir=initialdir
        )
        if path:
            self.game_entry.delete(0, ctk.END)
            self.game_entry.insert(0, path)

    def _pick_output(self):
        initialdir = str(Path.home() / "Downloads")
        path = filedialog.askdirectory(
            title=self._t("select_output_folder"), initialdir=initialdir
        )
        if path:
            self.output_entry.delete(0, ctk.END)
            self.output_entry.insert(0, path)
            self._save_output_root(path)

    def _load_settings(self):
        try:
            if CONFIG_PATH.is_file():
                cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
                output_root = cfg.get("output_root", "")
                if output_root:
                    self.output_entry.delete(0, ctk.END)
                    self.output_entry.insert(0, output_root)
        except Exception:
            pass

    def _save_output_root(self, path: str):
        try:
            cfg = {}
            if CONFIG_PATH.is_file():
                cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            cfg["output_root"] = str(Path(path).resolve())
            CONFIG_PATH.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _download_sdk(self):
        self._text_refs["convert"].configure(state="disabled")
        self._text_refs["sdk_download"].configure(state="disabled")
        self._clear_log()
        self._append_log(self._t("sdk_downloading"))
        self._set_status(self._t("sdk_downloading"))
        self.progress.start()
        thread = threading.Thread(target=self._run_download_sdk, daemon=True)
        thread.start()

    def _run_download_sdk(self):
        try:
            sdk_manager.download_sdk(progress_callback=self._download_progress)
            self.after(0, self._on_sdk_ready)
        except Exception as exc:
            self.after(0, self._on_sdk_error, str(exc))

    def _download_progress(self, downloaded: int, total: int):
        self.after(0, self._update_download_progress, downloaded, total)

    def _update_download_progress(self, downloaded: int, total: int):
        if total:
            pct = int(downloaded * 100 / total)
            self._set_status(f"{self._t('sdk_downloading')} {pct}%")
            self.progress.set(pct / 100)
        else:
            self._set_status(self._t("sdk_downloading"))

    def _on_sdk_ready(self):
        self.progress.stop()
        self.progress.set(0)
        self._set_status(self._t("sdk_ready"))
        self._append_log(self._t("sdk_ready"))
        self._text_refs["convert"].configure(state="normal")
        self._text_refs["sdk_download"].configure(text=self._t("sdk_update"))
        self._text_refs["sdk_download"].configure(state="normal")
        messagebox.showinfo(self._t("success_title"), self._t("sdk_ready"))

    def _on_sdk_error(self, message: str):
        self.progress.stop()
        self.progress.set(0)
        self._set_status(self._t("build_failed"))
        self._append_log(message)
        self._text_refs["convert"].configure(state="normal")
        self._text_refs["sdk_download"].configure(state="normal")
        messagebox.showerror(self._t("error"), message)

    def _cancel(self):
        if hasattr(self, "_cancel_event"):
            self._cancel_event.set()

    def _convert(self):
        game_raw = self.game_entry.get().strip()
        output_raw = self.output_entry.get().strip()

        if not game_raw:
            messagebox.showerror(self._t("error"), self._t("select_game"))
            return
        if not output_raw:
            messagebox.showerror(self._t("error"), self._t("select_output"))
            return

        game_path = Path(game_raw)
        if not game_path.exists():
            messagebox.showerror(self._t("error"), self._t("game_not_found").format(game_path))
            return

        data_dir = find_data_dir(game_path)
        if data_dir is None:
            messagebox.showerror(
                self._t("error"),
                self._t("data_not_found").format(game_path),
            )
            return

        # Calcola la sottocartella del progetto dal titolo del gioco.
        system_json = data_dir / "System.json"
        raw_title = "RPGM VN"
        if system_json.is_file():
            try:
                with open(system_json, "r", encoding="utf-8-sig") as f:
                    raw_title = json.load(f).get("gameTitle") or raw_title
            except Exception:
                pass
        safe_name = re.sub(r"[^A-Za-z0-9_-]", "_", raw_title).lower() or "rpgm_vn"
        project_dir = Path(output_raw) / safe_name

        options: dict = {"convert_dialogue_prefix": not self.no_prefix_var.get()}

        start_map = self.start_map_entry.get().strip()
        if start_map:
            try:
                options["start_map"] = int(start_map)
            except ValueError:
                messagebox.showerror(self._t("error"), self._t("start_map_error"))
                return

        include_events = self.include_events_entry.get().strip()
        if include_events:
            try:
                options["include_events"] = [
                    int(x) for x in re.split(r"[,\s]+", include_events) if x
                ]
            except ValueError:
                messagebox.showerror(self._t("error"), self._t("events_error"))
                return

        self._cancel_event = threading.Event()
        self._text_refs["cancel"].configure(state="normal")
        self._text_refs["convert"].configure(state="disabled")
        self._text_refs["sdk_download"].configure(state="disabled")
        self._clear_log()
        self._set_status(self._t("converting"))
        self.progress.start()

        thread = threading.Thread(
            target=self._run_convert_and_build,
            args=(data_dir, project_dir, options),
            daemon=True,
        )
        thread.start()

    def _run_convert_and_build(self, data_dir: Path, output_dir: Path, options: dict):
        try:
            generator = RenpyProjectGenerator(str(data_dir), str(output_dir), options, cancel_event=self._cancel_event)
            generator.generate()
            if self._cancel_event.is_set():
                self.after(0, self._on_build_error, "Conversione annullata dall'utente.")
                return
            self.after(0, self._append_log, self._t("conversion_done"))

            if not sdk_manager.is_sdk_present():
                self.after(0, self._set_status, self._t("sdk_downloading"))
                sdk_manager.download_sdk(progress_callback=self._download_progress)
                if self._cancel_event.is_set():
                    return

            self.after(0, self._set_status, self._t("building"))
            build_dir = output_dir / "dists"
            returncode, output = sdk_manager.build_project(
                output_dir,
                target=self._build_target_var.get(),
                destination=build_dir,
                log_callback=self._build_log,
                cancel_event=self._cancel_event,
            )
            if returncode == 0:
                self.after(0, self._on_build_success, output_dir, build_dir)
            else:
                self.after(0, self._on_build_error, output)
        except Exception as exc:
            self.after(0, self._on_build_error, str(exc))

    def _build_log(self, line: str):
        self.after(0, self._append_log, line)

    def _append_log(self, message: str):
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", message + "\n")
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")

    def _clear_log(self):
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", "end")
        self.log_textbox.configure(state="disabled")

    def _on_build_success(self, output_dir: Path, build_dir: Path):
        self.progress.stop()
        self.progress.set(0)
        self._set_status(f"✅ {self._t('build_success').format(build_dir)}")
        self._text_refs["convert"].configure(state="normal")
        self._text_refs["sdk_download"].configure(state="normal")
        self._text_refs["cancel"].configure(state="disabled")
        messagebox.showinfo(
            self._t("success_title"),
            self._t("build_success").format(build_dir),
        )

    def _on_build_error(self, message: str):
        self.progress.stop()
        self.progress.set(0)
        self._set_status(f"❌ {self._t('build_failed')}")
        self._text_refs["convert"].configure(state="normal")
        self._text_refs["sdk_download"].configure(state="normal")
        self._text_refs["cancel"].configure(state="disabled")
        self._append_log(message)
        messagebox.showerror(self._t("error"), message)


def main(argv=None):
    app = RenPGMakerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
