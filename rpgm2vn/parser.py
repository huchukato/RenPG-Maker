import json
import os
import re


class RpgmData:
    """Carica e indicizza i dati JSON di un progetto RPG Maker MV/MZ."""

    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.system = self._load_json("System.json") or {}
        self.mapinfos = self._load_json("MapInfos.json") or {}
        self.actors = self._load_json("Actors.json") or []
        self.common_events = self._load_json("CommonEvents.json") or []
        self.items = self._load_json("Items.json") or []
        self.weapons = self._load_json("Weapons.json") or []
        self.armors = self._load_json("Armors.json") or []
        self.skills = self._load_json("Skills.json") or []
        self.states = self._load_json("States.json") or []
        self.tilesets = self._load_json("Tilesets.json") or []
        self.animations = self._load_json("Animations.json") or []
        self.enemies = self._load_json("Enemies.json") or []
        self.troops = self._load_json("Troops.json") or []
        self.classes = self._load_json("Classes.json") or []
        self.map_cache = {}
        self._preload_maps()

    def _load_json(self, filename):
        path = os.path.join(self.data_dir, filename)
        if not os.path.isfile(path):
            return None
        with open(path, "r", encoding="utf-8-sig") as f:
            return json.load(f)

    def _preload_maps(self):
        if not os.path.isdir(self.data_dir):
            return
        for filename in os.listdir(self.data_dir):
            m = re.match(r"Map(\d+)\.json", filename)
            if not m:
                continue
            map_id = int(m.group(1))
            full_path = os.path.join(self.data_dir, filename)
            try:
                with open(full_path, "r", encoding="utf-8-sig") as f:
                    self.map_cache[map_id] = json.load(f)
            except Exception:
                pass

    def get_map(self, map_id):
        return self.map_cache.get(map_id)

    def list_map_ids(self):
        return sorted(self.map_cache.keys())

    def map_display_name(self, map_id):
        info = self.map_info(map_id)
        return info.get("name") or f"Map{map_id}"

    def map_info(self, map_id):
        if isinstance(self.mapinfos, dict):
            return self.mapinfos.get(str(map_id)) or self.mapinfos.get(map_id) or {}
        if isinstance(self.mapinfos, list) and map_id < len(self.mapinfos):
            return self.mapinfos[map_id] or {}
        return {}

    def get_common_event(self, ce_id):
        if isinstance(self.common_events, list):
            if 0 <= ce_id < len(self.common_events):
                return self.common_events[ce_id]
        elif isinstance(self.common_events, dict):
            return self.common_events.get(str(ce_id)) or self.common_events.get(ce_id)
        return None

    def get_actor(self, actor_id):
        if 1 <= actor_id <= len(self.actors):
            actor = self.actors[actor_id - 1]
            return actor or {}
        return {}

    def actor_name(self, actor_id):
        actor = self.get_actor(actor_id)
        return actor.get("name") or actor.get("nickname") or f"Actor{actor_id}"

    def actor_nick(self, actor_id):
        actor = self.get_actor(actor_id)
        return actor.get("nickname") or actor.get("name") or f"Actor{actor_id}"

    def actor_profile(self, actor_id):
        actor = self.get_actor(actor_id)
        return actor.get("profile") or ""

    def variable_name(self, var_id):
        variables = self.system.get("variables", [])
        if 1 <= var_id <= len(variables):
            name = variables[var_id - 1]
            if name:
                return name
        return f"var_{var_id}"

    def switch_name(self, switch_id):
        switches = self.system.get("switches", [])
        if 1 <= switch_id <= len(switches):
            name = switches[switch_id - 1]
            if name:
                return name
        return f"switch_{switch_id}"

    def game_title(self):
        return self.system.get("gameTitle") or "RPGM VN"

    def party_members(self):
        return self.system.get("partyMembers", [1])

    def start_map(self):
        return self.system.get("startMapId", 0)

    def start_position(self):
        return self.system.get("startX", 0), self.system.get("startY", 0)

    @staticmethod
    def safe_identifier(name):
        name = re.sub(r"[^0-9A-Za-z_]+", "_", name or "")
        name = re.sub(r"_+", "_", name).strip("_")
        if not name or name[0].isdigit():
            name = "_" + name
        return name
