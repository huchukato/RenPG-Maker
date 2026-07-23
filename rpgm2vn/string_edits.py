"""Persistenza delle modifiche manuali a dialoghi/scelte.

Il file strings_edits.json contiene due sezioni:
- rpgm: modifiche applicate ai dati RPG Maker prima della conversione.
- renpy: modifiche applicate allo script.rpy generato.
"""

import json
import os
from typing import Any


class StringEditsStore:
    """Carica/salva l'override delle stringhe in un file JSON."""

    FILENAME = "strings_edits.json"

    def __init__(self, project_dir: str):
        self.path = os.path.join(project_dir, self.FILENAME)

    def load(self) -> dict[str, Any]:
        if os.path.isfile(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"rpgm": {}, "renpy": {}}

    def save(self, data: dict[str, Any]) -> None:
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


def make_rpgm_sid(event_id: int, page_idx: int, cmd_idx: int, sub_idx: int | None = None) -> str:
    """Costruisce un ID stabile per una stringa RPG Maker.

    Formato: <event_id>:<page_idx>:<cmd_idx>[:<sub_idx>]
    """
    base = f"{event_id}:{page_idx}:{cmd_idx}"
    if sub_idx is not None:
        base += f":{sub_idx}"
    return base


def parse_rpgm_sid(sid: str) -> tuple[int, int, int, int | None]:
    parts = sid.split(":")
    if len(parts) == 3:
        return int(parts[0]), int(parts[1]), int(parts[2]), None
    if len(parts) == 4:
        return int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])
    raise ValueError(f"Invalid RPGM sid: {sid}")
