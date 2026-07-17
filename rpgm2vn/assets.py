import os
import re
import shutil


class AssetManager:
    """Copia asset grafici e audio dal gioco RPG Maker al progetto Ren'Py."""

    IMAGE_DIRS = [
        "img/parallaxes",
        "img/pictures",
        "img/faces",
        "img/characters",
        "img/sv_actors",
        "img/enemies",
        "img/battlebacks1",
        "img/battlebacks2",
        "img/titles1",
        "img/titles2",
    ]
    AUDIO_DIRS = [
        "audio/bgm",
        "audio/bgs",
        "audio/me",
        "audio/se",
    ]

    def __init__(self, project_root, output_dir):
        self.project_root = project_root
        self.output_dir = output_dir
        self.game_dir = os.path.join(output_dir, "game")
        self.images_dir = os.path.join(self.game_dir, "images")
        self.audio_dir = os.path.join(self.game_dir, "audio")

    def copy_assets(self):
        self._copy_category(self.IMAGE_DIRS, self.images_dir)
        self._copy_category(self.AUDIO_DIRS, self.audio_dir)

    def _copy_category(self, rel_dirs, dest_root):
        for rel in rel_dirs:
            src = os.path.join(self.project_root, rel)
            if not os.path.isdir(src):
                continue
            base = rel.split("/", 1)[1] if "/" in rel else rel
            dest = os.path.join(dest_root, base)
            os.makedirs(dest, exist_ok=True)
            for root, _, files in os.walk(src):
                for fname in files:
                    src_path = os.path.join(root, fname)
                    ext = os.path.splitext(fname)[1].lower()
                    if ext in (".rpgmvp", ".rpgmvo", ".rpgmvm", ".rpgmve"):
                        continue
                    rel_path = os.path.relpath(src_path, src)
                    safe_name = self._safe_filename(rel_path)
                    dst_path = os.path.join(dest, safe_name)
                    try:
                        shutil.copy2(src_path, dst_path)
                    except Exception:
                        pass

    def _safe_filename(self, name):
        parts = name.replace("\\", "/").split("/")
        safe = [re.sub(r"[^0-9A-Za-z_.-]", "_", p).strip("_.") for p in parts]
        safe = [p for p in safe if p]
        return "/".join(safe) if safe else "asset"
