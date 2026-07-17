import os
import re
import shutil
from .parser import RpgmData
from .transpiler import RenPyTranspiler
from .assets import AssetManager


class RenpyProjectGenerator:
    """Genera una cartella di progetto Ren'Py da un gioco RPG Maker."""

    def __init__(self, data_dir, output_dir, options=None):
        self.data_dir = data_dir
        self.output_dir = output_dir
        self.options = options or {}
        self.data = RpgmData(data_dir)
        self.transpiler = RenPyTranspiler(self.data, self.options)
        self.asset_manager = AssetManager(
            os.path.dirname(data_dir),  # assume data_dir is .../www/data
            output_dir
        )

    def generate(self):
        os.makedirs(self.output_dir, exist_ok=True)
        game_dir = os.path.join(self.output_dir, "game")
        os.makedirs(game_dir, exist_ok=True)

        # Pre-transpile all scripts and collect characters used.
        script_blocks, character_ids = self._build_scripts()

        # Write base definitions.
        with open(os.path.join(game_dir, "options.rpy"), "w", encoding="utf-8") as f:
            f.write(self._options_rpy())

        with open(os.path.join(game_dir, "script.rpy"), "w", encoding="utf-8") as f:
            f.write(self._script_rpy(character_ids, script_blocks))

        # Copy assets.
        self.asset_manager.copy_assets()

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

        return blocks, characters

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

    def _options_rpy(self):
        title = (self.data.game_title() or "RPGM VN").replace("\\", "\\\\").replace('"', '\\"')
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
'''

    def _script_rpy(self, character_ids, blocks):
        out = ["# Script generato da rpgm2vn", ""]
        max_vars = len(self.data.system.get("variables", []))
        max_sw = len(self.data.system.get("switches", []))
        for _i in range(1, max_vars + 1):
            out.append(f"default rpgm_var_{_i} = 0")
        for _i in range(1, max_sw + 1):
            out.append(f"default rpgm_switch_{_i} = False")
        out.append("default party_members = []")
        out.append("")

        # Character definitions
        for actor in self.data.actors:
            if not actor:
                continue
            name = actor.get("name") or actor.get("nickname") or ""
            aid = actor.get("id", 0)
            tag = f"actor_{aid}"
            out.append(f'define {tag} = Character({_escape_str(name)})')

        # Also define any other speakers encountered
        for cid in sorted(character_ids):
            if cid.startswith("actor_"):
                continue
            if cid == "narrator":
                continue
            out.append(f'define {cid} = Character({_escape_str(cid.replace("_", " ").title())})')

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

    def _escape_str(self, s):
        return _escape_str(s)


def _escape_str(s):
    s = (s or "").replace("\\", "\\\\")
    s = s.replace('"', '\\"')
    s = s.replace("\n", "\\n")
    return f'"{s}"'


