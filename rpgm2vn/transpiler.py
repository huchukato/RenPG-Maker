import re
from .parser import RpgmData


class RenPyTranspiler:
    """Converte i comandi evento RPG Maker in istruzioni Ren'Py."""

    COMMAND_NAMES = {
        0: "Null", 101: "Show Text", 102: "Show Choices", 103: "Input Number",
        104: "Choose Item", 105: "Show Scrolling Text", 108: "Comment",
        111: "Conditional Branch", 112: "Loop", 113: "Break Loop",
        115: "Exit Event Processing", 117: "Common Event", 118: "Label",
        119: "Jump To Label", 121: "Control Switches", 122: "Control Variables",
        123: "Control Self Switch", 124: "Control Timer", 125: "Change Gold",
        126: "Change Items", 127: "Change Weapons", 128: "Change Armors",
        129: "Change Party Member", 132: "Change Battle BGM", 133: "Change Victory ME",
        134: "Change Save Access", 135: "Toggle Menu Access", 136: "Change Encounter",
        137: "Change Formation", 138: "Change Window Color", 139: "Change Defeat ME",
        140: "Change Vehicle BGM", 201: "Transfer Map", 203: "Set Event Location",
        204: "Scroll Map", 205: "Set Movement Route", 211: "Change Transparency",
        212: "Show Character Animation", 213: "Show Balloon Icon", 214: "Erase Event",
        216: "Change Player Followers", 221: "Fade Out", 222: "Fade In",
        223: "Tint Screen", 224: "Flash Screen", 225: "Shake Screen", 230: "Wait",
        231: "Show Picture", 232: "Move Picture", 233: "Rotate Picture",
        234: "Tint Picture", 235: "Erase Picture", 236: "Set Weather Effect",
        241: "Play BGM", 242: "Fadeout BGM", 243: "Save BGM", 244: "Resume BGM",
        245: "Play BGS", 246: "Fadeout BGS", 249: "Play ME", 250: "Play SE",
        251: "Stop SE", 261: "Play Movie", 281: "Change Map Name",
        282: "Change Tileset", 283: "Change Battleback", 284: "Change Parallax",
        285: "Get Location Info", 301: "Battle", 302: "Shop",
        303: "Name Input", 311: "Change HP", 312: "Change MP", 313: "Change State",
        314: "Recover All", 315: "Change EXP", 316: "Change Level",
        317: "Change Parameter", 318: "Change Skill", 319: "Change Equipment",
        320: "Change Name", 321: "Change Class", 322: "Change Actor Images",
        323: "Change Vehicle Image", 324: "Change Nickname", 325: "Change Profile",
        326: "Change TP", 331: "Change Enemy HP", 332: "Change Enemy MP",
        333: "Change Enemy State", 334: "Enemy Recover All", 335: "Enemy Appear",
        336: "Enemy Transform", 337: "Show Battle Animation", 339: "Force Action",
        340: "Abort Battle", 342: "Change Enemy TP", 351: "Open Menu",
        352: "Open Save", 353: "Game Over", 354: "Return To Title",
        355: "Script", 356: "Plugin Command", 357: "Plugin Command (MZ)",
        401: "Show Text Continuation", 402: "When", 403: "When Cancel",
        404: "Choice End", 405: "Scrolling Text Continuation", 408: "Comment",
        411: "Else", 412: "End Branch", 413: "Repeat Above",
        505: "Movement Route Alternate", 601: "On Battle Win",
        602: "On Battle Escape", 603: "On Battle Lose",
        604: "End Battle Branch", 655: "Script Continuation",
        657: "Plugin Arg",
    }

    def __init__(self, data: RpgmData, options=None):
        self.data = data
        self.options = options or {}
        self.convert_dialogue_prefix = self.options.get("convert_dialogue_prefix", True)
        self.default_character = self.options.get("default_character", "narrator")

    def _indent(self, level):
        return "    " * level

    def _ensure_body(self, body, indent_level):
        if not body or not any(ln.strip() and not ln.strip().startswith('#') for ln in body):
            return [self._indent(indent_level) + "pass"]
        return body

    def transpile_map(self, map_id):
        map_data = self.data.get_map(map_id)
        if not map_data:
            return []
        events = [e for e in map_data.get("events", []) if e]
        blocks = []
        sorted_events = sorted(events, key=lambda e: e.get("id", 0))
        # Pre-transpile events to know which have content
        event_blocks = []
        for event in sorted_events:
            event_key = f"map{map_id:03d}_event{event.get('id', 0):03d}"
            event_lines = self._transpile_event(map_id, event)
            if event_lines:
                event_blocks.append((event_key, event_lines))
        if event_blocks:
            map_label = [f"label map{map_id:03d}:", "    $ renpy.pause(0, hard=False)"]
            for event_key, _ in event_blocks:
                map_label.append(f"    call {event_key}")
            map_label.append("    return")
            blocks.append((f"map{map_id:03d}", map_label))
            blocks.extend(event_blocks)
        else:
            blocks.append((f"map{map_id:03d}", [f"label map{map_id:03d}:", "    $ renpy.pause(0, hard=False)", "    return"]))
        return blocks

    def transpile_common_event(self, ce_id):
        ce = self.data.get_common_event(ce_id)
        if not ce:
            return []
        commands = ce.get("list", [])
        if not commands:
            return []
        lines = [f"label common_event_{ce_id}:"]
        body, _ = self._process_block(commands, 0, -1, 1, f"ce{ce_id}")
        if not body or body[-1].strip() != "return":
            body.append("    return")
        body.insert(0, "    $ renpy.pause(0, hard=False)")
        lines.extend(["    " + ln for ln in body])
        return lines

    def _transpile_event(self, map_id, event):
        event_id = event.get("id", 0)
        pages = event.get("pages", [])
        if not pages:
            return []
        page = pages[0]
        commands = page.get("list", [])
        ctx = f"m{map_id}_e{event_id}"
        body, _ = self._process_block(commands, 0, -1, 1, ctx)
        if not body:
            return []
        if body[-1].strip() != "return":
            body.append("    return")
        body.insert(0, "    $ renpy.pause(0, hard=False)")
        return [f"label map{map_id:03d}_event{event_id:03d}:"] + ["    " + ln for ln in body]

    def _process_block(self, commands, i, parent_editor_indent, renpy_indent, ctx):
        """Processa comandi finché indent <= parent_editor_indent."""
        out = []
        terminated = False
        pending_transition = None

        def _emit(s):
            for sub_line in s.split("\n"):
                out.append(self._indent(renpy_indent) + sub_line)

        while i < len(commands):
            cmd = commands[i]
            ci = cmd.get("indent", 0)
            cc = cmd.get("code", 0)
            if ci <= parent_editor_indent:
                break
            if terminated:
                i += 1
                continue
            if cc == 101:
                text, i = self._collect_text(commands, i, renpy_indent, ctx)
                pending_transition = None
                out.extend(text)
            elif cc == 111:
                pending_transition = None
                block, i = self._handle_if(commands, i, ci, renpy_indent, ctx)
                out.extend(block)
            elif cc == 112:
                pending_transition = None
                block, i = self._handle_loop(commands, i, ci, renpy_indent, ctx)
                out.extend(block)
            elif cc == 102:
                pending_transition = None
                block, i = self._handle_choice(commands, i, ci, renpy_indent, ctx)
                out.extend(block)
            elif cc == 113:
                pending_transition = None
                out.append(self._indent(renpy_indent) + "# break")
                i += 1
            elif cc == 115:
                pending_transition = None
                out.append(self._indent(renpy_indent) + "return")
                i += 1
                terminated = True
            elif cc in (0, 108, 408, 505, 657, 601, 602, 603, 604, 412, 413, 404, 411, 402, 403, 401):
                # terminators/options handled by their parents
                pending_transition = None
                i += 1
            else:
                line, _ = self._process_command(cmd, ctx)
                if line == "with fade":
                    pending_transition = "with fade"
                elif pending_transition:
                    if not line:
                        pending_transition = None
                    else:
                        first = line.split("\n")[0].strip()
                        if first.startswith(("show ", "hide ")):
                            _emit(line)
                            _emit(pending_transition)
                        else:
                            _emit(line)
                        pending_transition = None
                else:
                    if line:
                        _emit(line)
                        if line == "return":
                            terminated = True
                i += 1
        return out, i

    def _handle_if(self, commands, i, editor_indent, renpy_indent, ctx):
        cmd = commands[i]
        params = cmd.get("parameters", [])
        cond = self._build_condition(params)
        i += 1
        if cond == "True":
            body, i = self._process_block(commands, i, editor_indent, renpy_indent, ctx)
            # consume unreachable else
            if i < len(commands) and commands[i].get("code") == 411 and commands[i].get("indent") == editor_indent:
                i += 1
                _, i = self._process_block(commands, i, editor_indent, renpy_indent, ctx)
            if i < len(commands) and commands[i].get("code") == 412 and commands[i].get("indent") == editor_indent:
                i += 1
            return body, i
        out = [self._indent(renpy_indent) + f"if {cond}:"]
        body, i = self._process_block(commands, i, editor_indent, renpy_indent + 1, ctx)
        body = self._ensure_body(body, renpy_indent + 1)
        out.extend(body)
        # else
        if i < len(commands) and commands[i].get("code") == 411 and commands[i].get("indent") == editor_indent:
            out.append(self._indent(renpy_indent) + "else:")
            i += 1
            body, i = self._process_block(commands, i, editor_indent, renpy_indent + 1, ctx)
            body = self._ensure_body(body, renpy_indent + 1)
            out.extend(body)
        # consume end 412 if present at same editor indent
        if i < len(commands) and commands[i].get("code") == 412 and commands[i].get("indent") == editor_indent:
            i += 1
        return out, i

    def _handle_loop(self, commands, i, editor_indent, renpy_indent, ctx):
        # Ren'Py non supporta break/continue nei while script, quindi emettiamo il corpo una volta.
        i += 1
        body, i = self._process_block(commands, i, editor_indent, renpy_indent, ctx)
        if i < len(commands) and commands[i].get("code") in (413, 412) and commands[i].get("indent") == editor_indent:
            i += 1
        return body, i

    def _is_continue_choice(self, text):
        if not text:
            return False
        t = str(text).strip().lower().rstrip("?.!")
        return t == "continue"

    def _handle_choice(self, commands, i, editor_indent, renpy_indent, ctx):
        cmd = commands[i]
        params = cmd.get("parameters", [])
        choices = params[0] if len(params) > 0 else []
        cancel_type = params[2] if len(params) > 2 else 0

        # Scelta singola "Continue?" -> appiattisce il corpo senza menu
        if len(choices) == 1:
            raw_text = choices[0]
            display = self._format_text(raw_text) if raw_text else ""
            if self._is_continue_choice(display):
                i += 1
                while i < len(commands):
                    c = commands[i]
                    ci = c.get("indent", 0)
                    cc = c.get("code", 0)
                    if ci < editor_indent:
                        break
                    if cc == 402:
                        i += 1
                        body, i = self._process_block(commands, i, editor_indent, renpy_indent, ctx)
                        return (body, i) if body else ([], i)
                    elif cc == 404:
                        i += 1
                        break
                    else:
                        i += 1
                return [], i

        out = [self._indent(renpy_indent) + "menu:"]
        i += 1
        option_level = renpy_indent + 1
        while i < len(commands):
            c = commands[i]
            ci = c.get("indent", 0)
            cc = c.get("code", 0)
            if ci < editor_indent:
                # terminatore
                break
            if cc == 402:
                idx = c.get("parameters", [0, ""])[0]
                text = choices[idx] if 0 <= idx < len(choices) else ""
                text = self._format_text(text)
                out.append(self._indent(option_level) + f'"{text}":')
                i += 1
                body, i = self._process_block(commands, i, editor_indent, option_level + 1, ctx)
                body = self._ensure_body(body, option_level + 1)
                out.extend(body)
            elif cc == 403:
                out.append(self._indent(option_level) + '"Cancel":')
                i += 1
                body, i = self._process_block(commands, i, editor_indent, option_level + 1, ctx)
                body = self._ensure_body(body, option_level + 1)
                out.extend(body)
            elif cc == 404:
                i += 1
                break
            else:
                # body senza option? ignora
                i += 1
        return out, i

    def _collect_text(self, commands, i, renpy_indent, ctx):
        cmd = commands[i]
        params = cmd.get("parameters", [])
        face_name = params[0] if len(params) > 0 else ""
        speaker = params[4] if len(params) > 4 else ""
        lines = []
        i += 1
        while i < len(commands) and commands[i].get("code") == 401:
            lines.append(str(commands[i].get("parameters", [""])[0]))
            i += 1
        text = "\\n".join(lines)
        if not text:
            return [], i
        char = self._resolve_speaker(speaker, face_name)
        return [self._indent(renpy_indent) + f'{char} "{self._format_text(text)}"'], i

    def _resolve_speaker(self, speaker, face_name):
        if speaker:
            return self._safe_identifier(speaker)
        if face_name:
            return self._safe_identifier(face_name)
        return self.default_character

    def _process_command(self, cmd, ctx):
        code = cmd.get("code", 0)
        params = cmd.get("parameters", [])
        if code == 117:
            ce_id = params[0] if params else 0
            return f"call common_event_{ce_id}", None
        if code == 118:
            return f"# label label_{self._safe(params[0]) if params else 'x'}:", None
        if code == 119:
            return f"# jump label_{self._safe(params[0]) if params else 'x'}", None
        if code == 121:
            return "\n".join(self._handle_control_switches(params)), None
        if code == 122:
            return "\n".join(self._handle_control_variables(params)), None
        if code == 123:
            return "\n".join(self._handle_self_switch(params, ctx)), None
        if code in (125, 126, 127, 128):
            return "\n".join(self._handle_inventory(code, params)), None
        if code == 129:
            return "\n".join(self._handle_party(params)), None
        if code in (132, 133, 134, 135, 136, 137, 138, 139, 140):
            return "", None
        if code == 201:
            return "\n".join(self._handle_transfer(params)), None
        if code in (203, 204, 205, 211, 212, 213, 214, 216):
            return "", None
        if code == 210:
            return self._handle_wait(params, 20), None
        if code == 230:
            return self._handle_wait(params, 60), None
        if code in (221, 222):
            return "with fade", None
        if code == 223:
            return "with dissolve", None
        if code == 224:
            return "with flash", None
        if code == 225:
            return "with vpunch", None
        if code == 231:
            return self._handle_show_picture(params), None
        if code in (232, 233, 234):
            return "", None
        if code == 235:
            return self._handle_erase_picture(params), None
        if code == 236:
            return "", None
        if code == 241:
            return self._handle_play_bgm(params), None
        if code == 242:
            return "stop music fadeout 2.0", None
        if code == 243:
            return "$ _saved_bgm = renpy.music.get_playing(channel='music')", None
        if code == 244:
            return "play music _saved_bgm", None
        if code == 245:
            return self._handle_play_bgs(params), None
        if code == 246:
            return "stop sound fadeout 2.0", None
        if code == 249:
            return self._handle_play_me(params), None
        if code == 250:
            return self._handle_play_se(params), None
        if code == 251:
            return "stop sound", None
        if code == 261:
            return self._handle_movie(params), None
        if code in (281, 282, 283, 284, 285):
            return "", None
        if code in (301, 302, 311, 312, 313, 314, 315, 316, 317, 318, 319, 326,
                    331, 332, 333, 334, 335, 336, 337, 339, 340, 342):
            return f"# battle/system {code}", None
        if code == 303:
            return self._handle_name_input(params), None
        if code in (320, 321, 322, 323, 324, 325):
            return "\n".join(self._handle_actor_change(code, params)), None
        if code in (351, 352):
            return f"# {self.COMMAND_NAMES.get(code, code)}", None
        if code in (353, 354):
            return "return", None
        if code == 355:
            return "\n".join(self._handle_script(params, ctx)), None
        if code == 356:
            return "\n".join(self._handle_plugin_command(params)), None
        if code == 357:
            return "\n".join(self._handle_plugin_command_mz(params)), None
        if code == 655:
            return "", None
        if code == 105:
            return self._handle_scrolling_text(params), None
        if code == 405:
            return "", None
        return f"# RPGM cmd {code}: {repr(params)[:80]}", None

    def _handle_scrolling_text(self, params):
        if not params:
            return ""
        text = str(params[0])
        return f'narrator "{self._format_text(text)}"'

    def _build_condition(self, params):
        if not params:
            return "True"
        op = params[0]
        if op == 0:
            sw = params[1]
            val = params[2] == 0 if len(params) > 2 else True
            return f"rpgm_switch_{sw}" if val else f"not rpgm_switch_{sw}"
        if op == 1:
            v1 = params[1]
            comp = params[2] if len(params) > 2 else 0
            op_type = params[3] if len(params) > 3 else 0
            value = params[4] if len(params) > 4 else 0
            left = f"rpgm_var_{v1}"
            right = self._var_operand(op_type, value)
            ops = {0: "==", 1: ">=", 2: "<=", 3: ">", 4: "<", 5: "!="}
            return f"{left} {ops.get(comp, '==')} {right}"
        if op == 2:
            return f"rpgm_selfswitch_{params[1]}"
        if op == 3:
            return "True"
        if op == 4:
            return f"({params[1]} in party_members)"
        if op in (5, 6, 7, 8, 9, 10, 11):
            return "True"
        return "True"

    def _var_operand(self, val_type, val):
        if val_type == 0:
            if isinstance(val, str):
                return self._quote_str(val)
            return str(val)
        if val_type == 1:
            return f"rpgm_var_{val}"
        if val_type == 2:
            return "0"
        if val_type == 3:
            return str(val)
        if val_type == 4:
            if isinstance(val, str):
                return self._quote_str(val)
            return str(val)
        return str(val)

    def _handle_control_switches(self, params):
        start, end, value = (params + [0, 0, 0])[:3]
        lines = []
        for sw in range(start, end + 1):
            py_val = "True" if value == 0 else "False"
            lines.append(f"$ rpgm_switch_{sw} = {py_val}")
        return lines

    def _handle_control_variables(self, params):
        start = params[0] if len(params) > 0 else 0
        end = params[1] if len(params) > 1 else start
        operation = params[2] if len(params) > 2 else 0
        op_type = params[3] if len(params) > 3 else 0
        op_value = params[4] if len(params) > 4 else 0
        op_value2 = params[5] if len(params) > 5 else 0
        right = self._var_right_side(op_type, op_value, op_value2)
        ops = {0: "=", 1: "+=", 2: "-=", 3: "*=", 4: "/=", 5: "%="}
        op_symbol = ops.get(operation, "=")
        lines = []
        for v in range(start, end + 1):
            lines.append(f"$ rpgm_var_{v} {op_symbol} {right}")
        return lines

    def _var_right_side(self, op_type, op_value, op_value2=0):
        if op_type == 0:
            if isinstance(op_value, str):
                return self._quote_str(op_value)
            return str(op_value)
        if op_type == 1:
            return f"rpgm_var_{op_value}"
        if op_type == 2:
            return f"renpy.random.randint({op_value}, {op_value2})"
        if op_type == 3:
            return "0"
        if op_type == 4:
            if isinstance(op_value, str):
                return self._quote_str(op_value)
            return str(op_value)
        return str(op_value)

    def _handle_self_switch(self, params, ctx):
        if not params:
            return []
        ch = params[0]
        value = params[1] if len(params) > 1 else 0
        return [f"$ {self._safe_identifier(ctx)}_ss_{ch} = {'True' if value == 0 else 'False'}"]

    def _handle_inventory(self, code, params):
        return [f"# inventory op {code} {params}"]

    def _handle_party(self, params):
        if not params:
            return []
        actor_id, action = params[0], params[1] if len(params) > 1 else 0
        name = self.data.actor_name(actor_id)
        if action == 0:
            return [
                f"$ party_members.append({actor_id})",
                f'narrator "{name} si unisce al gruppo."',
            ]
        return [f"$ party_members.remove({actor_id}) if {actor_id} in party_members else None"]

    def _handle_transfer(self, params):
        if not params or len(params) < 2:
            return ["return"]
        # MZ Transfer Player: [vehicle, mapId, x, y, direction, fadeType]
        map_id = params[1]
        if map_id == 0 or map_id not in self.data.map_cache:
            return ["return"]
        return [f"call map{map_id:03d}"]

    def _handle_wait(self, params, fps=60):
        duration = params[0] if params else 60
        seconds = max(0.0, duration / fps)
        return f"with Pause({seconds:.2f})"

    def _handle_show_picture(self, params):
        if not params:
            return ""
        pic_id = params[0]
        pic_name = params[1] if len(params) > 1 else ""
        tag = self._safe_identifier(pic_name) or f"pic_{pic_id}"
        return f"show {tag}"

    def _handle_erase_picture(self, params):
        pic_id = params[0] if params else 1
        return f"hide pic_{pic_id}"

    def _handle_play_bgm(self, params):
        bgm = params[0] if params else {}
        name = bgm.get("name", "") if isinstance(bgm, dict) else bgm
        if not name:
            return ""
        return f'play music "{self._safe_filename(name)}"'

    def _handle_play_bgs(self, params):
        bgs = params[0] if params else {}
        name = bgs.get("name", "") if isinstance(bgs, dict) else bgs
        if not name:
            return ""
        return f'play sound "{self._safe_filename(name)}" loop'

    def _handle_play_me(self, params):
        me = params[0] if params else {}
        name = me.get("name", "") if isinstance(me, dict) else me
        if not name:
            return ""
        return f'play sound "{self._safe_filename(name)}"'

    def _handle_play_se(self, params):
        se = params[0] if params else {}
        name = se.get("name", "") if isinstance(se, dict) else se
        if not name:
            return ""
        return f'play sound "{self._safe_filename(name)}"'

    def _handle_movie(self, params):
        if not params:
            return ""
        filename = params[0] if isinstance(params[0], str) else (params[0].get("name", "") if isinstance(params[0], dict) else "")
        return f'$ rpgm_play_movie("movies/{self._safe_filename(filename)}")'

    def _handle_name_input(self, params):
        actor_id = params[0] if params else 0
        max_chars = params[1] if len(params) > 1 else 8
        default_name = self.data.actor_name(actor_id)
        return f'$ actor_{actor_id}_name = renpy.input("Inserisci un nome:", default="{default_name}", length={max_chars})'

    def _handle_actor_change(self, code, params):
        if not params:
            return []
        actor_id = params[0]
        name = self.data.actor_name(actor_id)
        if code == 320 and len(params) > 1:
            return [
                f'$ actor_{actor_id}_name = {self._quote_str(params[1])}',
                f'narrator "{name} ora si chiama [actor_{actor_id}_name]."',
            ]
        if code == 321:
            return [f"# cambia classe di {name}"]
        if code == 322:
            return [f"# cambia grafica di {name}"]
        if code == 324 and len(params) > 1:
            return [f'$ actor_{actor_id}_nickname = {self._quote_str(params[1])}']
        if code == 325 and len(params) > 1:
            return [f'$ actor_{actor_id}_profile = {self._quote_str(params[1])}']
        return [f"# actor change {code} {params}"]

    def _handle_script(self, params, ctx):
        if not params:
            return []
        script = params[0]
        if isinstance(script, list):
            script = "\n".join(script)
        return self._interpret_javascript(script, ctx)

    def _interpret_javascript(self, script, ctx):
        script = script.strip()
        if not script:
            return []
        if script.startswith("//"):
            return []
        m = re.search(r"\$gameVariables\.setValue\(\s*(\d+)\s*,\s*(['\"`])(.*?)\2\s*\)", script, re.S)
        if m:
            var_id = int(m.group(1))
            text = m.group(3)
            if var_id == 21 and self.convert_dialogue_prefix:
                return self._dialogue_from_variable(text)
            return [f"$ rpgm_var_{var_id} = {self._quote_str(text)}"]
        m2 = re.search(r"\$gameSwitches\.setValue\(\s*(\d+)\s*,\s*(true|false|0|1)\s*\)", script, re.I)
        if m2:
            sw = int(m2.group(1))
            val = m2.group(2).lower() in ("true", "1")
            return [f"$ rpgm_switch_{sw} = {val}"]
        return [f"# JS: {script}"]

    def _dialogue_from_variable(self, text):
        text = self._unescape(text)
        m = re.match(r"^([A-Za-z0-9_]+)\.(.*)$", text, re.S)
        if m:
            prefix = m.group(1)
            body = m.group(2)
            speaker = self._speaker_from_prefix(prefix)
            return [f'{speaker} "{self._format_text(body)}"']
        return [f'{self.default_character} "{self._format_text(text)}"']

    def _speaker_from_prefix(self, prefix):
        tokens = re.findall(r"[A-Z][a-z]*|[A-Z]+", prefix)
        if not tokens:
            return self.default_character
        name = tokens[0]
        return self._safe_identifier(name).lower()

    def _handle_plugin_command(self, params):
        if not params:
            return []
        cmd = params[0] if isinstance(params[0], str) else str(params[0])
        return [f"# Plugin: {cmd}"]

    def _handle_plugin_command_mz(self, params):
        if not params:
            return []
        plugin = params[0] if params else ""
        cmd = params[1] if len(params) > 1 else ""
        if plugin == "DK_Video_Player":
            args = params[3] if len(params) > 3 and isinstance(params[3], dict) else {}
            src = self._safe_filename(args.get("src", ""))
            loop = str(args.get("loop", "true")).lower() in ("true", "1", "yes")
            wait = str(args.get("wait", "false")).lower() in ("true", "1", "yes")
            if cmd == "LoadVideo" and src:
                return [f'$ _renpg_video = rpgm_movie_path("movies/{src}")']
            if cmd == "PlayVideo":
                lines = []
                if src:
                    lines.append(f'$ _renpg_video = rpgm_movie_path("movies/{src}")')
                if wait:
                    lines.append("if _renpg_video:")
                    lines.append("    $ rpgm_play_movie(_renpg_video)")
                else:
                    lines.append("if _renpg_video:")
                    loop_arg = f", loop={loop}" if not loop else ""
                    lines.append(f'    show expression Transform(Movie(play=_renpg_video{loop_arg}), xysize=(config.screen_width, config.screen_height), fit="contain", xalign=0.5, yalign=0.5) as renpg_video')
                return lines
            if cmd == "StopVideo":
                return ["hide renpg_video"]
        return [f"# MZ Plugin {plugin}: {cmd}"]

    def _format_text(self, text):
        if text is None:
            return ""
        text = self._unescape(text)
        text = text.replace("\\", "\\\\")
        text = text.replace('"', '\\"')
        # Escape Ren'Py interpolation and text tag characters
        text = text.replace("[", "[[")
        text = text.replace("{", "{{")
        text = text.replace("%", "%%")
        text = text.replace("\n", "\\n")
        text = text.replace("\r", "")
        # Ripristina le sequenze \n (raddoppiate sopra) affinché Ren'Py le interpreti come a capo.
        text = text.replace("\\\\n", "\\n")
        return text

    def _unescape(self, text):
        if isinstance(text, bytes):
            text = text.decode("utf-8", "ignore")
        return text

    def _quote_str(self, s):
        s = self._unescape(s)
        s = s.replace("\\", "\\\\")
        s = s.replace('"', '\\"')
        s = s.replace("%", "%%")
        s = s.replace("\n", "\\n")
        # Ripristina le sequenze \n (raddoppiate sopra) affinché Ren'Py le interpreti come a capo.
        s = s.replace("\\\\n", "\\n")
        return f'"{s}"'

    def _safe(self, s):
        return self._safe_identifier(str(s))

    RESERVED = {
        "as", "at", "with", "menu", "label", "jump", "call", "return", "if", "else", "elif",
        "while", "for", "in", "not", "and", "or", "True", "False", "None", "python",
        "init", "default", "define", "transform", "image", "show", "hide", "scene",
        "play", "stop", "queue", "voice", "pause", "window", "screen", "break",
        "continue", "pass", "return", "class", "def", "global", "nonlocal", "lambda",
        "try", "except", "finally", "raise", "assert", "del", "from", "import",
        "is", "yield", "async", "await",
    }

    def _safe_identifier(self, name):
        name = re.sub(r"[^0-9A-Za-z_]+", "_", name or "")
        name = re.sub(r"_+", "_", name).strip("_")
        if not name or name[0].isdigit():
            name = "_" + name
        if name.lower() in self.RESERVED:
            name = "_" + name
        return name

    def _safe_filename(self, name):
        return re.sub(r"[^0-9A-Za-z_.-]+", "_", name or "").strip("_.")
