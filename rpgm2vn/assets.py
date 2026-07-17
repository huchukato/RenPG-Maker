import os
import re
import shutil


class AssetManager:
    """Copia e decripta asset grafici, audio e video dal gioco RPG Maker al progetto Ren'Py."""

    RPGM_HEADER_LEN = 16
    ENCRYPTED_EXTS = {
        ".rpgmvp": ".png",
        ".rpgmvo": ".ogg",
        ".rpgmvm": ".mp4",
        ".rpgmve": ".wav",
    }

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
    MOVIE_DIRS = [
        "movies",
    ]

    def __init__(self, project_root, output_dir, encryption_key=None, cancel_event=None):
        self.project_root = project_root
        self.output_dir = output_dir
        self.encryption_key = encryption_key
        self.cancel_event = cancel_event
        self.game_dir = os.path.join(output_dir, "game")
        self.images_dir = os.path.join(self.game_dir, "images")
        self.audio_dir = os.path.join(self.game_dir, "audio")
        self.movies_dir = os.path.join(self.game_dir, "movies")

    def copy_assets(self):
        self._copy_category(self.IMAGE_DIRS, self.images_dir)
        self._copy_category(self.AUDIO_DIRS, self.audio_dir)
        self._copy_category(self.MOVIE_DIRS, self.movies_dir)

    def _copy_category(self, rel_dirs, dest_root):
        for rel in rel_dirs:
            if self.cancel_event and self.cancel_event.is_set():
                return
            src = os.path.join(self.project_root, rel)
            if not os.path.isdir(src):
                continue
            base = rel.split("/", 1)[1] if "/" in rel else ""
            dest = os.path.join(dest_root, base)
            os.makedirs(dest, exist_ok=True)
            for root, _, files in os.walk(src):
                for fname in files:
                    if self.cancel_event and self.cancel_event.is_set():
                        return
                    src_path = os.path.join(root, fname)
                    ext = os.path.splitext(fname)[1].lower()
                    rel_path = os.path.relpath(src_path, src)
                    safe_name = self._safe_filename(rel_path)
                    dst_path = os.path.join(dest, safe_name)
                    if ext in self.ENCRYPTED_EXTS:
                        if self.encryption_key:
                            self._decrypt_file(src_path, dst_path, ext)
                        continue
                    try:
                        shutil.copy2(src_path, dst_path)
                    except Exception:
                        pass

    def _decrypt_file(self, src_path, dst_path, encrypted_ext):
        """Decripta un file RPG Maker MV/MZ."""
        key = bytes.fromhex(self.encryption_key)
        if len(key) < self.RPGM_HEADER_LEN:
            return
        try:
            with open(src_path, "rb") as f:
                data = f.read()
            if len(data) <= self.RPGM_HEADER_LEN:
                return
            payload = bytearray(data[self.RPGM_HEADER_LEN :])
            for i in range(self.RPGM_HEADER_LEN):
                payload[i] ^= key[i]
            out_ext = self._detect_extension(bytes(payload[:32]), encrypted_ext)
            base = os.path.splitext(dst_path)[0]
            final_path = base + out_ext
            with open(final_path, "wb") as f:
                f.write(payload)
        except Exception:
            pass

    def _detect_extension(self, first_bytes, encrypted_ext):
        """Determina l'estensione originale dal contenuto decrittato."""
        if first_bytes[:8] == b"\x89PNG\r\n\x1a\n":
            return ".png"
        if first_bytes[:4] == b"OggS":
            return ".ogg"
        if first_bytes[:4] == b"RIFF":
            return ".wav"
        if first_bytes[:4] == b"\x1a\x45\xdf\xa3":
            return ".webm"
        if len(first_bytes) >= 8 and first_bytes[4:8] == b"ftyp":
            if encrypted_ext == ".rpgmvo":
                return ".m4a"
            return ".mp4"
        return self.ENCRYPTED_EXTS.get(encrypted_ext, ".bin")

    def _safe_filename(self, name):
        parts = name.replace("\\", "/").split("/")
        safe = [re.sub(r"[^0-9A-Za-z_.-]", "_", p).strip("_.") for p in parts]
        safe = [p for p in safe if p]
        return "/".join(safe) if safe else "asset"
