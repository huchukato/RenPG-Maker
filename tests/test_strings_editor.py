import json
import os
import tempfile
import unittest
from pathlib import Path

from rpgm2vn import strings_editor
from rpgm2vn.string_edits import StringEditsStore, make_rpgm_sid, parse_rpgm_sid


class TestStringEdits(unittest.TestCase):
    def test_store_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = StringEditsStore(tmp)
            data = {
                "rpgm": {
                    "Map001.json": {
                        "1:0:5": {"text": "Ciao", "deleted": False},
                        "1:0:6": {"deleted": True},
                    }
                },
                "renpy": {
                    "script.rpy": {
                        "42": {"text": "Hello", "deleted": False},
                        "43": {"deleted": True},
                    }
                },
            }
            store.save(data)
            loaded = store.load()
            self.assertEqual(loaded["rpgm"]["Map001.json"]["1:0:5"]["text"], "Ciao")
            self.assertTrue(loaded["rpgm"]["Map001.json"]["1:0:6"]["deleted"])
            self.assertEqual(loaded["renpy"]["script.rpy"]["42"]["text"], "Hello")


class TestRpgmExtraction(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_extract_dialogue_and_choice(self):
        map_data = {
            "events": [
                None,
                {
                    "id": 1,
                    "pages": [
                        {
                            "list": [
                                {"code": 101, "parameters": ["", 0, 0, 2, "Guard"], "indent": 0},
                                {"code": 401, "parameters": ["Hello miss."], "indent": 0},
                                {"code": 102, "parameters": [["Yes", "No"], 1, 0, 2, 0], "indent": 0},
                                {"code": 402, "parameters": [0, "Yes"], "indent": 0},
                                {"code": 0, "parameters": [], "indent": 1},
                                {"code": 402, "parameters": [1, "No"], "indent": 0},
                                {"code": 0, "parameters": [], "indent": 1},
                                {"code": 404, "parameters": [], "indent": 0},
                            ]
                        }
                    ]
                }
            ]
        }
        (self.data_dir / "Map001.json").write_text(json.dumps(map_data), encoding="utf-8")
        items = strings_editor.extract_rpgm_strings(str(self.data_dir))
        kinds = [i.kind for i in items]
        self.assertIn("dialogue", kinds)
        self.assertIn("choice", kinds)
        dialogue = next(i for i in items if i.kind == "dialogue")
        self.assertEqual(dialogue.original, "Hello miss.")
        self.assertEqual(dialogue.speaker, "Guard")
        choices = [i for i in items if i.kind == "choice"]
        self.assertEqual([c.original for c in choices], ["Yes", "No"])


class TestRenpyExtraction(unittest.TestCase):
    def test_extract_script(self):
        script = '''label start:
    narrator "Welcome."
    Alice "Hi there!"
    menu:
        "Yes":
            pass
        "No":
            pass
'''
        with tempfile.TemporaryDirectory() as tmp:
            script_path = Path(tmp) / "script.rpy"
            script_path.write_text(script, encoding="utf-8")
            items = strings_editor.extract_renpy_script(str(script_path))
        self.assertEqual(len(items), 4)
        self.assertEqual(items[0].kind, "narrator")
        self.assertEqual(items[0].original, "Welcome.")
        self.assertEqual(items[1].kind, "dialogue")
        self.assertEqual(items[1].speaker, "Alice")
        choices = [i for i in items if i.kind == "choice"]
        self.assertEqual(len(choices), 2)


class TestApplyEdits(unittest.TestCase):
    def test_apply_renpy_edits(self):
        lines = [
            '    narrator "Welcome.",\n',
            '    Alice "Hi there!"\n',
            '        "Yes":\n',
        ]
        edits = {
            "1": {"text": "Good day."},
            "2": {"deleted": True},
        }
        result = strings_editor.apply_edits_to_script_lines(lines, edits)
        self.assertIn('    narrator "Good day.",\n', result)
        self.assertNotIn('    Alice "Hi there!"\n', result)
        self.assertEqual(len(result), 2)

    def test_apply_rpgm_choice_edit(self):
        data = {
            "events": [
                {
                    "id": 1,
                    "pages": [
                        {
                            "list": [
                                {"code": 102, "parameters": [["Yes", "No"], 1, 0, 2, 0], "indent": 0},
                            ]
                        }
                    ]
                }
            ]
        }
        sid = make_rpgm_sid(1, 0, 0, 0)
        strings_editor.apply_edits_to_rpgm_data(data, {sid: {"text": "Sure"}})
        self.assertEqual(data["events"][0]["pages"][0]["list"][0]["parameters"][0][0], "Sure")

    def test_apply_rpgm_delete_choice(self):
        data = {
            "events": [
                {
                    "id": 1,
                    "pages": [
                        {
                            "list": [
                                {"code": 102, "parameters": [["Yes", "No"], 1, 0, 2, 0], "indent": 0},
                            ]
                        }
                    ]
                }
            ]
        }
        sid = make_rpgm_sid(1, 0, 0, 1)
        strings_editor.apply_edits_to_rpgm_data(data, {sid: {"deleted": True}})
        self.assertEqual(data["events"][0]["pages"][0]["list"][0]["parameters"][0], ["Yes"])

    def test_apply_rpgm_delete_last_choice_removes_command(self):
        data = {
            "events": [
                {
                    "id": 1,
                    "pages": [
                        {
                            "list": [
                                {"code": 102, "parameters": [["Yes"], 1, 0, 2, 0], "indent": 0},
                            ]
                        }
                    ]
                }
            ]
        }
        sid = make_rpgm_sid(1, 0, 0, 0)
        strings_editor.apply_edits_to_rpgm_data(data, {sid: {"deleted": True}})
        self.assertEqual(len(data["events"][0]["pages"][0]["list"]), 0)


if __name__ == "__main__":
    unittest.main()
