import os
import re
import shutil
from pathlib import Path
from .parser import RpgmData
from .transpiler import RenPyTranspiler
from .assets import AssetManager
from .map_renderer import MapRenderer
from .string_edits import StringEditsStore
from .strings_editor import apply_edits_to_rpgm_data, apply_edits_to_script_lines


class RenpyProjectGenerator:
    """Genera una cartella di progetto Ren'Py da un gioco RPG Maker."""

    def __init__(self, data_dir, output_dir, options=None, template_dir=None, cancel_event=None):
        self.data_dir = data_dir
        self.output_dir = output_dir
        self.options = options or {}
        self.cancel_event = cancel_event

        self.data = RpgmData(data_dir)
        self.output_width, self.output_height = self._output_size()

        # Template base integrato nel package (o custom passato dal chiamante).
        if template_dir:
            self.template_dir = template_dir
        else:
            template_name = "720" if self.output_height <= 720 else "1080"
            self.template_dir = str(
                Path(__file__).resolve().parent / "templates" / template_name / "game"
            )

        self.transpiler = RenPyTranspiler(self.data, self.options)
        encryption_key = self.data.system.get("encryptionKey") if self.data.system.get("hasEncryptedImages") or self.data.system.get("hasEncryptedAudio") else None
        self.asset_manager = AssetManager(
            os.path.dirname(data_dir),  # assume data_dir is .../www/data
            output_dir,
            encryption_key=encryption_key,
            cancel_event=self.cancel_event,
        )

    def generate(self):
        if self.cancel_event and self.cancel_event.is_set():
            return
        os.makedirs(self.output_dir, exist_ok=True)
        game_dir = os.path.join(self.output_dir, "game")
        os.makedirs(game_dir, exist_ok=True)

        # Template GUI and screens (optional).
        if self.template_dir:
            self._copy_template(game_dir)

        # Splash screen.
        self._copy_splash(game_dir)
        self._write_splash_rpy(game_dir)

        if self.cancel_event and self.cancel_event.is_set():
            return

        # Applica eventuali modifiche manuali ai dati RPG Maker (in memoria).
        edits_store = StringEditsStore(self.output_dir)
        edits = edits_store.load()
        rpgm_edits = edits.get("rpgm", {})
        if rpgm_edits:
            for filename, file_edits in rpgm_edits.items():
                if filename == "CommonEvents.json" and self.data.common_events:
                    apply_edits_to_rpgm_data(self.data.common_events, file_edits)
                elif filename.startswith("Map") and filename.endswith(".json"):
                    try:
                        map_id = int(filename[3:-5])
                    except ValueError:
                        continue
                    map_data = self.data.get_map(map_id)
                    if map_data:
                        apply_edits_to_rpgm_data(map_data, file_edits)

        # Pre-transpile all scripts and collect characters used.
        script_blocks, character_ids, character_faces = self._build_scripts()

        # Render map backgrounds and insert scene commands at map labels.
        map_bg_ids = self._render_map_backgrounds(game_dir)
        self._insert_map_scenes(script_blocks, map_bg_ids)

        if self.cancel_event and self.cancel_event.is_set():
            return

        # Write base definitions.
        with open(os.path.join(game_dir, "options.rpy"), "w", encoding="utf-8") as f:
            f.write(self._options_rpy())

        script_content = self._script_rpy(character_ids, character_faces, map_bg_ids, script_blocks)
        renpy_edits = edits.get("renpy", {}).get("script.rpy", {})
        if renpy_edits:
            script_lines = script_content.splitlines()
            script_lines = apply_edits_to_script_lines(script_lines, renpy_edits)
            script_content = "\n".join(script_lines)
        with open(os.path.join(game_dir, "script.rpy"), "w", encoding="utf-8") as f:
            f.write(script_content)

        # Copy assets.
        self.asset_manager.copy_assets()

        # Image definitions.
        self._write_images_rpy(game_dir)

        # Menu backgrounds.
        self._copy_menu_backgrounds(game_dir)

    def _build_scripts(self):
        blocks = {}
        characters = set()
        # Common events first.
        ce_ids = []
        if isinstance(self.data.common_events, list):
            for i, ce in enumerate(self.data.common_events):
                if ce:
                    ce_ids.append(i)
        elif isinstance(self.data.common_events, dict):
            for k in self.data.common_events:
                try:
                    ce_ids.append(int(k))
                except ValueError:
                    pass
        for ce_id in sorted(ce_ids):
            lines = self.transpiler.transpile_common_event(ce_id)
            if lines:
                blocks[f"common_event_{ce_id}"] = lines
                characters.update(self._collect_characters(lines))

        # Maps.
        for map_id in self.data.list_map_ids():
            result = self.transpiler.transpile_map(map_id)
            if result:
                if isinstance(result, list) and isinstance(result[0], tuple):
                    for key, lines in result:
                        blocks[key] = lines
                        characters.update(self._collect_characters(lines))
                else:
                    blocks[f"map{map_id:03d}"] = result
                    characters.update(self._collect_characters(result))

        return blocks, characters, self.transpiler.character_faces

    def _render_map_backgrounds(self, game_dir):
        """Render map PNGs and return the set of map ids that succeeded."""
        try:
            renderer = MapRenderer(self.data)
            target = (self.output_width, self.output_height)
            return renderer.render_all(game_dir, target_size=target)
        except Exception:
            return set()

    def _insert_map_scenes(self, script_blocks, map_bg_ids):
        """Prepend scene map_bg_<id> to each map label block."""
        for map_id in sorted(map_bg_ids):
            key = f"map{map_id:03d}"
            if key not in script_blocks:
                continue
            lines = script_blocks[key]
            if not lines:
                continue
            # Insert the scene right after the label line.
            scene_line = f"    scene map_bg_{map_id:03d}"
            if len(lines) > 1:
                lines.insert(1, scene_line)
            else:
                lines.append(scene_line)

    def _collect_characters(self, lines):
        ids = set()
        for ln in lines:
            m = re.match(r'^[ \t]*([A-Za-z_][A-Za-z0-9_]*)\s+"', ln)
            if m:
                tag = m.group(1)
                if tag not in ("label", "scene", "show", "hide", "call", "jump", "with", "play", "stop", "menu", "return", "if", "else", "elif", "while", "pass"):
                    ids.add(tag)
            m2 = re.search(r"^\s*define\s+([A-Za-z_][A-Za-z0-9_]*)\s*=", ln)
            if m2:
                ids.add(m2.group(1))
        return ids

    def _output_size(self):
        width = self.options.get("output_width")
        height = self.options.get("output_height")
        if width is None or height is None:
            width, height = self.data.window_size()
        try:
            width = int(width)
            height = int(height)
        except (TypeError, ValueError):
            return 1920, 1080
        if width <= 0 or height <= 0:
            return 1920, 1080
        return width, height

    def _options_rpy(self):
        raw_title = self.data.game_title() or "RPGM VN"
        title = raw_title.replace("\\", "\\\\").replace('"', '\\"')
        safe_name = re.sub(r"[^A-Za-z0-9_-]", "_", raw_title).lower() or "rpgm_vn"
        width, height = self.output_width, self.output_height
        bgm_name = self.data.title_bgm_name()
        main_menu_music_line = ""
        if bgm_name:
            safe_bgm = self.asset_manager._safe_filename(bgm_name + ".ogg")
            main_menu_music_line = f'    config.main_menu_music = "audio/bgm/{safe_bgm}"\n'
        return f'''# Opzioni generate da rpgm2vn
init -1 python:
    config.name = "{title}"
    config.version = "1.0.0"

    gui.show_name = False
    config.has_voice = False
    config.has_music = True
    config.has_sound = True
    config.enter_transition = dissolve
    config.exit_transition = dissolve
    config.intra_transition = dissolve
    config.window = "auto"
{main_menu_music_line}    config.screen_width = {width}
    config.screen_height = {height}
    config.default_fullscreen = False

init python:
    build.name = "{safe_name}"
    build.version = "1.0.0"
    build.directory_name = "{safe_name}-1.0.0"
    build.executable_name = "{safe_name}"

    build.package("pc", "zip", "windows linux mac renpy all")
    build.package("win", "zip", "windows renpy all")
    build.package("mac", "app-zip", "mac renpy all")
    build.package("linux", "tar.bz2", "linux renpy all")

    def rpgm_play_movie(base):
        if base and "." in base.rsplit("/", 1)[-1] and renpy.loadable(base):
            renpy.movie_cutscene(base)
            return
        for ext in (".mp4", ".webm", ".ogv", ".mkv"):
            path = base + ext
            if renpy.loadable(path):
                renpy.movie_cutscene(path)
                return

    def rpgm_movie_path(base):
        name = base.rsplit("/", 1)[-1]
        if "." in name:
            return base if renpy.loadable(base) else None
        for ext in (".mp4", ".webm", ".ogv", ".mkv"):
            path = base + ext
            if renpy.loadable(path):
                return path
        return None
'''

    def _script_rpy(self, character_ids, character_faces, map_bg_ids, blocks):
        out = ["# Script generato da rpgm2vn", ""]
        max_vars = len(self.data.system.get("variables", []))
        max_sw = len(self.data.system.get("switches", []))
        out.append("default rpgm_var_0 = 0")
        for _i in range(1, max_vars + 1):
            out.append(f"default rpgm_var_{_i} = 0")
        for _i in range(1, max_sw + 1):
            out.append(f"default rpgm_switch_{_i} = False")
        out.append("default party_members = []")
        out.append("default _renpg_video = None")
        out.append("define flash = Fade(0.1, 0.1, 0.1, color='#fff')")
        out.append("")

        # Character definitions
        for actor in self.data.actors:
            if not actor:
                continue
            name = actor.get("name") or actor.get("nickname") or ""
            aid = actor.get("id", 0)
            tag = f"actor_{aid}"
            out.append(f'define {tag} = Character({_escape_str(name)})')
            out.append(f'default {tag}_name = {_escape_str(name)}')

        # Also define any other speakers encountered
        for cid in sorted(character_ids):
            if cid.startswith("actor_"):
                continue
            if cid == "narrator":
                continue
            img_arg = f', image="{cid}"' if cid in character_faces else ""
            out.append(f'define {cid} = Character({_escape_str(cid.replace("_", " ").title())}{img_arg})')

        # Side images for faces
        for tag, face_name in sorted(character_faces.items()):
            if tag and face_name:
                out.append(f'image {tag} = "faces/{face_name}"')

        # Map backgrounds
        for map_id in sorted(map_bg_ids):
            out.append(f'image map_bg_{map_id:03d} = "map_bg/map_{map_id:03d}.png"')

        out.append("")

        # start label
        start_map = self.data.start_map()
        out.append("label start:")
        if start_map and start_map in self.data.map_cache:
            out.append(f"    jump map{start_map:03d}")
        else:
            first_map = self.data.list_map_ids()[0] if self.data.list_map_ids() else 1
            out.append(f"    jump map{first_map:03d}")
        out.append("")

        for key in sorted(blocks):
            out.extend(blocks[key])
            out.append("")

        return "\n".join(out) + "\n"

    def _copy_template(self, game_dir):
        """Copia tutto il template base Ren'Py nella cartella game di output.

        Prima rimuove i file esistenti per evitare che un template a 1080
        lasci residui (es. immagini gui) in un progetto generato a 720.
        """
        game_path = Path(game_dir)
        if game_path.is_dir():
            for entry in game_path.iterdir():
                if entry.is_dir():
                    shutil.rmtree(entry, ignore_errors=True)
                else:
                    try:
                        entry.unlink()
                    except OSError:
                        pass
        src = Path(self.template_dir) if self.template_dir else None
        if not src or not src.is_dir():
            raise FileNotFoundError(f"Template base non trovato: {self.template_dir}")
        if (src / "game").is_dir():
            src = src / "game"
        shutil.copytree(
            src,
            Path(game_dir),
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns(
                "cache", "saves", "*.rpyc", "*.rpyb", "*.rpymc", ".DS_Store", ".gitignore"
            ),
        )
        gui_path = Path(game_dir) / "gui.rpy"
        if gui_path.is_file():
            gui_text = gui_path.read_text(encoding="utf-8")
            gui_text = re.sub(
                r"gui\.init\(\d+, \d+\)",
                f"gui.init({self.output_width}, {self.output_height})",
                gui_text,
                count=1,
            )
            gui_path.write_text(gui_text, encoding="utf-8")

    def _copy_splash(self, game_dir):
        splash_src = Path(__file__).resolve().parent.parent / "img" / "splash.png"
        if splash_src.exists():
            try:
                shutil.copy2(str(splash_src), os.path.join(game_dir, "renpg_splash.png"))
            except Exception:
                pass

    def _write_splash_rpy(self, game_dir):
        splash_path = os.path.join(game_dir, "splash.rpy")
        with open(splash_path, "w", encoding="utf-8") as f:
            f.write('''image renpg_splash = "renpg_splash.png"

label before_main_menu:
    if renpy.session.get("_renpg_splash_shown"):
        return
    $ renpy.session["_renpg_splash_shown"] = True
    scene black
    with Pause(0.5)
    show renpg_splash at Transform(xysize=(config.screen_width, config.screen_height), fit="contain", xalign=0.5, yalign=0.5)
    with dissolve
    pause 2.5
    hide renpg_splash
    with dissolve
    return
''')

    def _write_images_rpy(self, game_dir):
        images_dir = os.path.join(game_dir, "images")
        if not os.path.isdir(images_dir):
            return
        out_lines = ["# Auto-generated image definitions\n\n"]
        seen = set()
        for root, dirs, files in os.walk(images_dir):
            dirs.sort()
            if os.path.basename(root) == "map_bg":
                continue
            for fname in sorted(files):
                ext = os.path.splitext(fname)[1].lower()
                if ext not in (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".avif"):
                    continue
                full = os.path.join(root, fname)
                rel = os.path.relpath(full, game_dir).replace("\\", "/")
                raw_tag = re.sub(r"^(bg[_-]|!)", "", os.path.splitext(fname)[0], flags=re.I)
                tag = self.transpiler._safe_identifier(raw_tag)
                if not tag or tag == "_" or tag in seen:
                    continue
                seen.add(tag)
                out_lines.append(f'image {tag} = "{rel}"\n')
        out_path = os.path.join(game_dir, "images.rpy")
        with open(out_path, "w", encoding="utf-8") as f:
            f.writelines(out_lines)

    def _copy_menu_backgrounds(self, game_dir):
        title1 = self.data.title1_name()
        title2 = self.data.title2_name()
        if not title1:
            return
        images_dir = os.path.join(game_dir, "images")
        gui_dir = os.path.join(game_dir, "gui")
        if not os.path.isdir(images_dir):
            return
        os.makedirs(gui_dir, exist_ok=True)

        def find_image(safe_stem):
            for fname in os.listdir(images_dir):
                base, ext = os.path.splitext(fname)
                if base == safe_stem and ext.lower() in (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"):
                    return fname
            return None

        safe1 = os.path.splitext(self.asset_manager._safe_picture_name(f"{title1}.png"))[0]
        match1 = find_image(safe1)
        if not match1:
            return
        src1 = os.path.join(images_dir, match1)
        shutil.copy2(src1, os.path.join(gui_dir, "main_menu.png"))
        if title2:
            safe2 = os.path.splitext(self.asset_manager._safe_picture_name(f"{title2}.png"))[0]
            match2 = find_image(safe2)
            if match2:
                shutil.copy2(os.path.join(images_dir, match2), os.path.join(gui_dir, "game_menu.png"))
                return
        shutil.copy2(src1, os.path.join(gui_dir, "game_menu.png"))

    def _escape_str(self, s):
        return _escape_str(s)


def _escape_str(s):
    s = (s or "").replace("\\", "\\\\")
    s = s.replace('"', '\\"')
    s = s.replace("\n", "\\n")
    return f'"{s}"'


