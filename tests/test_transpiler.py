import json
import tempfile
import unittest
from pathlib import Path

from rpgm2vn.generator import RenpyProjectGenerator
from rpgm2vn.plugins import DKVideoPlayerPlugin, PluginDispatcher
from rpgm2vn.transpiler import RenPyTranspiler


class BuildConditionTests(unittest.TestCase):
    def setUp(self):
        self.transpiler = RenPyTranspiler(None)

    def test_variable_condition_with_constant(self):
        self.assertEqual(
            self.transpiler._build_condition([1, 162, 0, 5, 1]),
            "rpgm_var_162 >= 5",
        )

    def test_variable_condition_with_variable_operand(self):
        self.assertEqual(
            self.transpiler._build_condition([1, 161, 1, 162, 5]),
            "rpgm_var_161 != rpgm_var_162",
        )


class OutputResolutionTests(unittest.TestCase):
    def _generator(self, options=None):
        temp_dir = tempfile.TemporaryDirectory()
        root = Path(temp_dir.name)
        data_dir = root / "data"
        data_dir.mkdir()
        (data_dir / "System.json").write_text(
            json.dumps({"gameTitle": "Test Game"}), encoding="utf-8"
        )
        generator = RenpyProjectGenerator(
            str(data_dir), str(root / "output"), options or {}
        )
        return temp_dir, generator

    def test_default_output_is_1920_by_1080(self):
        temp_dir, generator = self._generator()
        self.addCleanup(temp_dir.cleanup)
        options = generator._options_rpy()
        self.assertEqual((generator.output_width, generator.output_height), (1920, 1080))
        self.assertIn("config.screen_width = 1920", options)
        self.assertIn("config.screen_height = 1080", options)

    def test_template_gui_uses_configured_output_size(self):
        temp_dir, generator = self._generator(
            {"output_width": 1280, "output_height": 720}
        )
        self.addCleanup(temp_dir.cleanup)
        game_dir = Path(temp_dir.name) / "game"
        generator._copy_template(str(game_dir))
        gui = (game_dir / "gui.rpy").read_text(encoding="utf-8")
        screens = (game_dir / "screens.rpy").read_text(encoding="utf-8")
        options = generator._options_rpy()
        self.assertIn("gui.init(1280, 720)", gui)
        self.assertIn('fit="cover"', screens)
        self.assertIn("config.screen_width = 1280", options)
        self.assertIn("config.screen_height = 720", options)


class PluginTests(unittest.TestCase):
    def setUp(self):
        self.transpiler = RenPyTranspiler(None)

    def test_dk_video_player_play_blocking(self):
        result = self.transpiler._handle_plugin_command_mz(
            ["DK_Video_Player", "PlayVideo", 0, {"src": "Hidden_Scene_1", "loop": "false", "wait": "false"}]
        )
        self.assertIn("rpgm_play_movie(_renpg_video)", "\n".join(result))
        self.assertNotIn("loop=True", "\n".join(result))

    def test_dk_video_player_play_looping(self):
        result = self.transpiler._handle_plugin_command_mz(
            ["DK_Video_Player", "PlayVideo", 0, {"src": "Menu_BG", "loop": "true", "wait": "false"}]
        )
        self.assertIn("loop=True", "\n".join(result))

    def test_unknown_plugin_is_commented(self):
        result = self.transpiler._handle_plugin_command_mz(
            ["Unknown_Plugin", "DoStuff", 0, {"x": 1}]
        )
        self.assertTrue(any(line.startswith("# MZ Plugin") for line in result))

    def test_ysp_video_player_play_by_id(self):
        result = self.transpiler._interpret_javascript(
            "ysp.VideoPlayer.newVideo('Intro', 1); ysp.VideoPlayer.playVideoById(1);", None
        )
        self.assertIn("rpgm_play_movie(_renpg_video)", "\n".join(result))

    def test_ysp_video_player_loop_by_id(self):
        result = self.transpiler._interpret_javascript(
            "ysp.VideoPlayer.newVideo('MenuLoop', 2); ysp.VideoPlayer.setLoopById(2); ysp.VideoPlayer.playVideoById(2);", None
        )
        self.assertIn("loop=True", "\n".join(result))


class VarRefTests(unittest.TestCase):
    def setUp(self):
        self.transpiler = RenPyTranspiler(None)

    def test_variable_condition_zero_id_becomes_literal(self):
        self.assertEqual(self.transpiler._build_condition([1, 0, 0, 0, 0]), "0 == 0")
        self.assertEqual(self.transpiler._build_condition([1, 5, 1, 0, 5]), "rpgm_var_5 != 0")

    def test_variable_operand_zero_id_becomes_literal(self):
        self.assertEqual(self.transpiler._var_operand(1, 0), "0")
        self.assertEqual(self.transpiler._var_operand(1, 7), "rpgm_var_7")


class ShowPictureTests(unittest.TestCase):
    def setUp(self):
        self.transpiler = RenPyTranspiler(None)

    def test_show_picture_lowercases_and_replaces_dash(self):
        self.assertEqual(self.transpiler._handle_show_picture([1, "MSG-DarkBG"]), "show msg_darkbg")

    def test_show_picture_bg_prefix_uses_scene(self):
        self.assertEqual(self.transpiler._handle_show_picture([2, "BG-forest"]), "scene forest")
        self.assertEqual(self.transpiler._handle_show_picture([3, "!Splash"]), "scene splash")

    def test_show_picture_act_background_uses_scene(self):
        self.assertEqual(self.transpiler._handle_show_picture([4, "Act 1/10"]), "scene act_1_10")

    def test_show_picture_intro_cg_uses_scene(self):
        self.assertEqual(self.transpiler._handle_show_picture([5, "intro_16"]), "scene intro_16")

    def test_show_picture_intro_slash_uses_scene(self):
        self.assertEqual(self.transpiler._handle_show_picture([5, "Intro/16"]), "scene intro_16")

    def test_erase_scene_picture_clears_scene(self):
        self.transpiler._handle_show_picture([1, "BG-forest"])
        self.assertEqual(self.transpiler._handle_erase_picture([1]), "scene")


if __name__ == "__main__":
    unittest.main()
