"""Estrazione e modifica di dialoghi/scelte dai dati RPG Maker e dallo script Ren'Py.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .string_edits import make_rpgm_sid, parse_rpgm_sid


@dataclass
class StringItem:
    sid: str
    kind: str  # dialogue, narrator, choice, comment
    source_file: str
    speaker: str
    original: str
    edited: str = ""
    deleted: bool = False
    line: int = -1
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def display_text(self) -> str:
        return self.edited if self.edited else self.original


# ────────────────────────── RPG Maker ──────────────────────────

def extract_rpgm_strings(data_dir: str) -> list[StringItem]:
    """Estrae dialoghi, narrazioni e scelte dai file Map*.json e CommonEvents.json."""
    items: list[StringItem] = []
    data_path = Path(data_dir)
    if not data_path.is_dir():
        return items

    for map_file in sorted(data_path.glob("Map[0-9]*.json")):
        try:
            data = json.loads(map_file.read_text(encoding="utf-8-sig"))
        except Exception:
            continue
        items.extend(_extract_from_map_data(data, map_file.name))

    common_file = data_path / "CommonEvents.json"
    if common_file.is_file():
        try:
            data = json.loads(common_file.read_text(encoding="utf-8-sig"))
        except Exception:
            data = []
        items.extend(_extract_from_common_events(data, "CommonEvents.json"))

    return items


def _extract_from_map_data(data: dict[str, Any], filename: str) -> list[StringItem]:
    items: list[StringItem] = []
    events = data.get("events") or []
    for event in events:
        if not event:
            continue
        event_id = event.get("id", 0)
        for page_idx, page in enumerate(event.get("pages", [])):
            items.extend(_extract_from_command_list(
                page.get("list", []), filename, event_id=event_id, page_idx=page_idx
            ))
    return items


def _extract_from_common_events(data: list[Any], filename: str) -> list[StringItem]:
    items: list[StringItem] = []
    for ce_id, ce in enumerate(data):
        if not ce:
            continue
        items.extend(_extract_from_command_list(
            ce.get("list", []), filename, event_id=ce_id, page_idx=0
        ))
    return items


def _extract_from_command_list(
    commands: list[dict[str, Any]],
    filename: str,
    event_id: int,
    page_idx: int,
) -> list[StringItem]:
    items: list[StringItem] = []
    speaker = ""
    for cmd_idx, cmd in enumerate(commands):
        code = cmd.get("code", 0)
        params = cmd.get("parameters", [])

        if code == 101:
            # Header Show Text: [faceName, faceIndex, background, position, speaker]
            speaker = params[4] if len(params) > 4 and params[4] else ""
            continue

        if code in (401, 405):
            text = params[0] if params else ""
            if not text:
                continue
            kind = "narrator" if not speaker else "dialogue"
            sid = make_rpgm_sid(event_id, page_idx, cmd_idx)
            items.append(StringItem(
                sid=sid,
                kind=kind,
                source_file=filename,
                speaker=speaker or "",
                original=str(text),
            ))
            continue

        if code == 102:
            choices = params[0] if params else []
            for sub_idx, choice in enumerate(choices):
                if not choice:
                    continue
                sid = make_rpgm_sid(event_id, page_idx, cmd_idx, sub_idx)
                items.append(StringItem(
                    sid=sid,
                    kind="choice",
                    source_file=filename,
                    speaker="",
                    original=str(choice),
                ))
            continue

        if code in (108, 408):
            text = params[0] if params else ""
            if text:
                sid = make_rpgm_sid(event_id, page_idx, cmd_idx)
                items.append(StringItem(
                    sid=sid,
                    kind="comment",
                    source_file=filename,
                    speaker="",
                    original=str(text),
                ))
    return items


# ────────────────────────── Ren'Py script ──────────────────────────

_RE_SAY = re.compile(r'^(\s*)([A-Za-z_][A-Za-z0-9_]*)\s+"((?:[^"\\]|\\.)*)"')
_RE_CHOICE = re.compile(r'^(\s*)"((?:[^"\\]|\\.)*)"\s*:')


def extract_renpy_script(script_path: str) -> list[StringItem]:
    """Estrae dialoghi, narrazioni e scelte dallo script.rpy generato."""
    items: list[StringItem] = []
    path = Path(script_path)
    if not path.is_file():
        return items
    lines = path.read_text(encoding="utf-8").splitlines()
    for idx, raw in enumerate(lines, start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue

        m_choice = _RE_CHOICE.match(raw)
        if m_choice:
            items.append(StringItem(
                sid=str(idx),
                kind="choice",
                source_file=path.name,
                speaker="",
                original=m_choice.group(2),
                line=idx,
            ))
            continue

        m_say = _RE_SAY.match(raw)
        if m_say:
            speaker = m_say.group(2)
            kind = "narrator" if speaker == "narrator" else "dialogue"
            items.append(StringItem(
                sid=str(idx),
                kind=kind,
                source_file=path.name,
                speaker=speaker,
                original=m_say.group(3),
                line=idx,
            ))
    return items


# ────────────────────────── Apply edits ──────────────────────────

def apply_edits_to_rpgm_data(data: dict[str, Any], edits: dict[str, Any]) -> None:
    """Applica le modifiche RPG Maker in-place al dizionario dati caricato."""
    for sid_str, change in edits.items():
        deleted = change.get("deleted", False)
        new_text = change.get("text")
        try:
            event_id, page_idx, cmd_idx, sub_idx = parse_rpgm_sid(sid_str)
        except ValueError:
            continue

        # Trova il comando
        cmd = _find_command(data, event_id, page_idx, cmd_idx)
        if cmd is None:
            continue

        code = cmd.get("code", 0)
        params = cmd.get("parameters", [])

        if deleted:
            _delete_rpgm_command(data, event_id, page_idx, cmd_idx, sub_idx)
            continue

        if new_text is None:
            continue

        if code in (401, 405, 108, 408):
            if params:
                params[0] = new_text
        elif code == 102 and sub_idx is not None and params:
            choices = params[0] if params else []
            if isinstance(choices, list) and 0 <= sub_idx < len(choices):
                choices[sub_idx] = new_text


def _find_command(
    data: dict[str, Any], event_id: int, page_idx: int, cmd_idx: int
) -> dict[str, Any] | None:
    source = data.get("events") if "events" in data else data if isinstance(data, list) else None
    if source is None:
        return None

    if "events" in data:
        for event in source:
            if event and event.get("id") == event_id:
                pages = event.get("pages", [])
                if page_idx < len(pages):
                    cmds = pages[page_idx].get("list", [])
                    if cmd_idx < len(cmds):
                        return cmds[cmd_idx]
        return None

    # CommonEvents.json è una lista
    if event_id < len(source):
        cmds = source[event_id].get("list", [])
        if cmd_idx < len(cmds):
            return cmds[cmd_idx]
    return None


def _delete_rpgm_command(
    data: dict[str, Any], event_id: int, page_idx: int, cmd_idx: int, sub_idx: int | None
) -> None:
    source = data.get("events") if "events" in data else data if isinstance(data, list) else None
    if source is None:
        return

    if "events" in data:
        for event in source:
            if event and event.get("id") == event_id:
                pages = event.get("pages", [])
                if page_idx < len(pages):
                    cmds = pages[page_idx].get("list", [])
                    _remove_from_list(cmds, cmd_idx, sub_idx)
                return
        return

    if event_id < len(source):
        cmds = source[event_id].get("list", [])
        _remove_from_list(cmds, cmd_idx, sub_idx)


def _remove_from_list(cmds: list[Any], cmd_idx: int, sub_idx: int | None) -> None:
    if cmd_idx >= len(cmds):
        return
    cmd = cmds[cmd_idx]
    code = cmd.get("code", 0)
    params = cmd.get("parameters", [])
    if code == 102 and sub_idx is not None:
        _remove_choice_branch(cmds, cmd_idx, sub_idx)
        return
    cmds.pop(cmd_idx)


def _remove_choice_branch(cmds: list[Any], cmd_idx: int, sub_idx: int) -> None:
    editor_indent = cmds[cmd_idx].get("indent", 0)

    # Rimuove la stringa della scelta dal comando 102
    params = cmds[cmd_idx].get("parameters", [])
    choices = params[0] if params else []
    if isinstance(choices, list) and 0 <= sub_idx < len(choices):
        choices.pop(sub_idx)

    # Trova gli inizi dei rami
    option_starts: list[int] = []
    j = cmd_idx + 1
    while j < len(cmds):
        c = cmds[j]
        ci = c.get("indent", 0)
        cc = c.get("code", 0)
        if ci < editor_indent:
            break
        if cc == 404 and ci == editor_indent:
            break
        if cc == 402 and ci == editor_indent:
            option_starts.append(j)
        j += 1

    # Se non ci sono rami 402 (es. dati minimi), rimuovi solo il comando se vuoto
    if not option_starts:
        if not choices:
            del cmds[cmd_idx]
            if cmd_idx < len(cmds) and cmds[cmd_idx].get("code") == 404 and cmds[cmd_idx].get("indent", 0) == editor_indent:
                del cmds[cmd_idx]
        return

    if sub_idx >= len(option_starts):
        return
    start = option_starts[sub_idx]
    # Trova la fine del ramo (prima del prossimo 402 o del 404)
    end = start + 1
    while end < len(cmds):
        c = cmds[end]
        ci = c.get("indent", 0)
        cc = c.get("code", 0)
        if ci == editor_indent and cc in (402, 404):
            break
        end += 1
    del cmds[start:end]

    # Rinumera i rami 402 successivi per allinearli alle nuove posizioni
    j = cmd_idx
    while j < len(cmds):
        c = cmds[j]
        ci = c.get("indent", 0)
        cc = c.get("code", 0)
        if ci < editor_indent:
            break
        if cc == 404 and ci == editor_indent:
            break
        if cc == 402 and ci == editor_indent:
            params = c.get("parameters", [0, ""])
            bidx = params[0] if params else 0
            if isinstance(bidx, int) and bidx > sub_idx:
                params[0] = bidx - 1
        j += 1

    if not choices:
        # Nessuna scelta rimasta: rimuovi anche il comando 102 e il 404 finale
        del cmds[cmd_idx]
        if cmd_idx < len(cmds) and cmds[cmd_idx].get("code") == 404 and cmds[cmd_idx].get("indent", 0) == editor_indent:
            del cmds[cmd_idx]


def apply_edits_to_script_lines(lines: list[str], edits: dict[str, Any]) -> list[str]:
    """Applica le modifiche Ren'Py a una lista di righe dello script."""
    # Lavoriamo in ordine inverso per mantenere validi gli indici
    line_numbers = sorted((int(k), v) for k, v in edits.items() if k.isdigit())
    for line_no, change in reversed(line_numbers):
        idx = line_no - 1
        if idx < 0 or idx >= len(lines):
            continue
        if change.get("deleted", False):
            deleted_line = lines[idx]
            lines.pop(idx)
            # Se la riga eliminata è un'opzione di menu, rimuovi anche il suo corpo
            # fino alla prossima opzione o alla fine del blocco menu.
            choice_match = _RE_CHOICE.match(deleted_line)
            if choice_match:
                choice_indent = len(choice_match.group(1))
                j = idx
                while j < len(lines):
                    line = lines[j]
                    if not line.strip():
                        j += 1
                        continue
                    if len(line) - len(line.lstrip()) <= choice_indent:
                        break
                    lines.pop(j)
            continue
        new_text = change.get("text")
        if new_text is None:
            continue
        lines[idx] = _replace_quoted_text(lines[idx], new_text)
    return lines


def _replace_quoted_text(line: str, new_text: str) -> str:
    """Sostituisce il testo tra la prima coppia di virgolette doppie in una riga."""
    start = line.find('"')
    if start == -1:
        return line
    end = start + 1
    escaped = False
    while end < len(line):
        ch = line[end]
        if escaped:
            escaped = False
        elif ch == "\\":
            escaped = True
        elif ch == '"':
            break
        end += 1
    else:
        return line
    return line[: start + 1] + new_text + line[end:]


# ────────────────────────── Load/save helper ──────────────────────────

def item_to_edit_record(item: StringItem) -> dict[str, Any]:
    change: dict[str, Any] = {"deleted": item.deleted}
    if item.edited:
        change["text"] = item.edited
    elif not item.deleted:
        # nessuna modifica
        return {}
    return change
