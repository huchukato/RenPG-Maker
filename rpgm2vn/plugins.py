import re
from typing import List, Optional


class RpgmPlugin:
    """Base per handler di plugin RPG Maker MV/MZ nel transpiler rpgm2vn."""

    # Tuple di nomi plugin (campo plugin del comando MZ) gestiti da questa classe.
    plugin_names = ()

    @classmethod
    def active(cls):
        return True

    @classmethod
    def process_command(
        cls,
        plugin_name: str,
        command: str,
        command_args: dict,
        transpiler: "RenPyTranspiler",
    ) -> Optional[List[str]]:
        """Restituisce le linee Ren'Py per un comando plugin, o None se non gestito."""
        return None

    @classmethod
    def process_script(
        cls, script: str, transpiler: "RenPyTranspiler"
    ) -> Optional[List[str]]:
        """Restituisce le linee Ren'Py per uno script JS, o None se non gestito."""
        return None


class DKVideoPlayerPlugin(RpgmPlugin):
    plugin_names = ("DK_Video_Player",)

    @classmethod
    def process_command(cls, plugin_name, command, command_args, transpiler):
        src = command_args.get("src", "")
        if isinstance(src, str):
            src = transpiler._safe_filename(src)
        loop = str(command_args.get("loop", "true")).lower() in ("true", "1", "yes")
        wait = str(command_args.get("wait", "false")).lower() in ("true", "1", "yes")

        if command == "LoadVideo" and src:
            return [f'$ _renpg_video = rpgm_movie_path("movies/{src}")']

        if command == "PlayVideo":
            lines = []
            if src:
                lines.append(f'$ _renpg_video = rpgm_movie_path("movies/{src}")')
            # I video non in loop o con wait devono bloccare il flusso,
            # altrimenti scompaiono dopo la pausa successiva.
            if wait or not loop:
                lines.append("if _renpg_video:")
                lines.append("    $ rpgm_play_movie(_renpg_video)")
            else:
                lines.append("if _renpg_video:")
                lines.append(
                    '    show expression Transform(Movie(play=_renpg_video, loop=True), '
                    'xysize=(config.screen_width, config.screen_height), fit="contain", xalign=0.5, yalign=0.5) as renpg_video'
                )
            return lines

        if command == "StopVideo":
            return ["hide renpg_video"]

        return None


class YspVideoPlayerPlugin(RpgmPlugin):
    """Gestisce le chiamate di script di YSP_VideoPlayer."""

    _CALL = re.compile(r"ysp\.VideoPlayer\.(\w+)\s*\(([^)]*)\)\s*;?")
    _ARG = re.compile(r"([\"'])([^\"']*)\1|(\d+)")

    @classmethod
    def _args(cls, arg_string):
        out = []
        for match in cls._ARG.finditer(arg_string):
            if match.group(2) is not None:
                out.append(match.group(2))
            else:
                out.append(int(match.group(3)))
        return out

    @classmethod
    def _video_lines(cls, name, loop, transpiler):
        safe = transpiler._safe_filename(name)
        lines = [f'$ _renpg_video = rpgm_movie_path("movies/{safe}")']
        if loop:
            lines.append("if _renpg_video:")
            lines.append(
                '    show expression Transform(Movie(play=_renpg_video, loop=True), '
                'xysize=(config.screen_width, config.screen_height), fit="contain", xalign=0.5, yalign=0.5) as renpg_video'
            )
        else:
            lines.append("if _renpg_video:")
            lines.append("    $ rpgm_play_movie(_renpg_video)")
        return lines

    @classmethod
    def process_script(cls, script, transpiler):
        if not hasattr(transpiler, "_ysp_videos"):
            transpiler._ysp_videos = {}
        if not hasattr(transpiler, "_ysp_video_loop"):
            transpiler._ysp_video_loop = set()

        lines = []
        found = False
        for match in cls._CALL.finditer(script):
            found = True
            method = match.group(1)
            args = cls._args(match.group(2))
            if method == "newVideo" and len(args) >= 2:
                name, vid_id = args[0], str(args[1])
                transpiler._ysp_videos[vid_id] = name
            elif method == "loadVideo" or method == "releaseVideo" or method == "isReady":
                # Nessun output Ren'Py necessario per preload/release/check.
                pass
            elif method == "playVideoById" and args:
                vid_id = str(args[0])
                name = transpiler._ysp_videos.get(vid_id)
                if name is not None:
                    loop = vid_id in transpiler._ysp_video_loop
                    lines.extend(cls._video_lines(name, loop, transpiler))
            elif method == "stopVideoById" and args:
                lines.append("hide renpg_video")
            elif method == "setLoopById" and args:
                transpiler._ysp_video_loop.add(str(args[0]))

        return lines if found else None


class PluginDispatcher:
    """Registra e dispone le chiamate agli handler plugin."""

    _builtins = [DKVideoPlayerPlugin, YspVideoPlayerPlugin]

    def __init__(self, transpiler: "RenPyTranspiler", extra_plugins=None):
        self.transpiler = transpiler
        self.handlers = {}
        self._all_handlers = []
        seen = set()
        for plugin_cls in list(self._builtins) + list(extra_plugins or []):
            if not plugin_cls.active():
                continue
            if plugin_cls not in seen:
                seen.add(plugin_cls)
                self._all_handlers.append(plugin_cls)
            for name in plugin_cls.plugin_names:
                self.handlers[name] = plugin_cls

    def handle_command(self, plugin_name: str, command: str, command_args: dict):
        handler = self.handlers.get(plugin_name)
        if handler is None:
            return None
        return handler.process_command(
            plugin_name, command, command_args, self.transpiler
        )

    def handle_script(self, script: str):
        for handler in self._all_handlers:
            result = handler.process_script(script, self.transpiler)
            if result is not None:
                return result
        return None
