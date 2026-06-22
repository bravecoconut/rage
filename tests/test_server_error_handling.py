import importlib.util
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"


def _load_server_module():
    """Import server.py without pulling in heavy stage dependencies."""
    for stage_num in range(1, 8):
        man = MagicMock()
        pkg = MagicMock()
        pkg.stage_1_man = man  # attribute access on package if needed
        sys.modules.setdefault(f"stage_{stage_num}", pkg)
        sys.modules[f"stage_{stage_num}.stage_{stage_num}_man"] = man

    spec = importlib.util.spec_from_file_location("server", APP / "server.py")
    server = importlib.util.module_from_spec(spec)
    sys.modules["server"] = server
    spec.loader.exec_module(server)
    return server


def parse_sse_events(raw: bytes):
    events = []
    for part in raw.split(b"\n\n"):
        part = part.strip()
        if part.startswith(b"data: "):
            events.append(json.loads(part[6:].decode("utf-8")))
    return events


class TestStageErrorHelpers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = _load_server_module()

    def test_is_stage_error(self):
        is_err = self.server._is_stage_error
        self.assertTrue(is_err(None))
        self.assertTrue(is_err({"error": ValueError("boom")}))
        self.assertFalse(is_err({"error": None}))
        self.assertFalse(is_err([{"topic": "fact"}]))
        self.assertFalse(is_err("research text"))
        self.assertFalse(is_err(42))
        self.assertFalse(is_err({"topic": "x", "description": "y"}))

    def test_error_status_payload_none_uses_fallback(self):
        payload = self.server._error_status_payload(None, "Failed to choose topic")
        self.assertEqual(payload, {"error_status": "Failed to choose topic"})

    def test_error_status_payload_dict_is_json_safe(self):
        payload = self.server._error_status_payload(
            {"error": ValueError("boom")},
            "fallback",
        )
        self.assertEqual(payload, {"error_status": "boom"})
        json.dumps(payload)

    def test_yield_stage_error_emits_data_and_flush(self):
        chunks = list(self.server._yield_stage_error(None, "Failed"))
        self.assertEqual(len(chunks), 2)
        self.assertTrue(chunks[0].startswith(b"data: "))
        self.assertEqual(chunks[1], b"")

        events = parse_sse_events(b"".join(chunks))
        self.assertEqual(events, [{"error_status": "Failed"}])


class TestStartEndpointErrors(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = _load_server_module()
        cls.app = cls.server.app
        cls.app.config["TESTING"] = True

    def _run_start(self, stage_patches):
        defaults = {
            "start_stage_1": MagicMock(return_value=[{"topic": "A fact"}]),
            "start_stage_2": MagicMock(return_value=0),
            "start_stage_3": MagicMock(return_value="research"),
            "start_stage_4": MagicMock(return_value="meme line"),
            "start_stage_5": MagicMock(return_value=123),
            "start_stage_6": MagicMock(return_value=123),
            "start_stage_7": MagicMock(
                return_value={
                    "topic": "A fact",
                    "description": "research",
                    "image_path": 123,
                    "poster": 123,
                }
            ),
        }
        defaults.update(stage_patches)

        patchers = [
            patch.object(self.server, name, mock)
            for name, mock in defaults.items()
        ]
        for patcher in patchers:
            patcher.start()
        self.addCleanup(lambda: [p.stop() for p in patchers])

        with patch("builtins.open", mock_open()):
            with self.app.test_client() as client:
                response = client.post("/start")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.mimetype, "text/event-stream")
                return parse_sse_events(response.get_data())

    def test_stage_1_error_dict(self):
        events = self._run_start(
            {"start_stage_1": MagicMock(return_value={"error": RuntimeError("scrape failed")})}
        )
        self.assertEqual(events[0], {"starting_status": {"stage_1": True}})
        self.assertEqual(events[-1], {"error_status": "scrape failed"})
        self.assertEqual(len(events), 2)

    def test_stage_1_empty_list(self):
        events = self._run_start({"start_stage_1": MagicMock(return_value=[])})
        self.assertEqual(events[-1], {"error_status": "Failed to fetch topics"})

    def test_stage_2_none(self):
        events = self._run_start({"start_stage_2": MagicMock(return_value=None)})
        self.assertEqual(events[0], {"starting_status": {"stage_1": True}})
        self.assertEqual(events[1], {"starting_status": {"stage_2": True}})
        self.assertEqual(events[-1], {"error_status": "Failed to choose topic"})

    def test_stage_3_error_dict(self):
        events = self._run_start(
            {"start_stage_3": MagicMock(return_value={"error": RuntimeError("research failed")})}
        )
        self.assertEqual(events[2], {"starting_status": {"stage_3": True}})
        self.assertEqual(events[-1], {"error_status": "research failed"})

    def test_stage_4_error_dict(self):
        events = self._run_start(
            {"start_stage_4": MagicMock(return_value={"error": RuntimeError("meme failed")})}
        )
        self.assertEqual(events[-1], {"error_status": "meme failed"})

    def test_stage_5_error_dict(self):
        events = self._run_start(
            {"start_stage_5": MagicMock(return_value={"error": RuntimeError("image failed")})}
        )
        self.assertEqual(events[-1], {"error_status": "image failed"})

    def test_stage_6_error_dict(self):
        events = self._run_start(
            {"start_stage_6": MagicMock(return_value={"error": RuntimeError("edit failed")})}
        )
        self.assertEqual(events[-1], {"error_status": "edit failed"})

    def test_stage_7_error_dict(self):
        events = self._run_start(
            {"start_stage_7": MagicMock(return_value={"error": RuntimeError("post failed")})}
        )
        self.assertEqual(events[-1], {"error_status": "post failed"})

    def test_success_yields_new_post(self):
        events = self._run_start({})
        self.assertEqual(events[0], {"starting_status": {"stage_1": True}})
        self.assertEqual(events[-1]["new_post"]["topic"], "A fact")
        self.assertNotIn("error_status", events[-1])

    def test_error_events_are_followed_by_flush_chunk(self):
        with patch.object(
            self.server,
            "start_stage_1",
            MagicMock(return_value={"error": RuntimeError("scrape failed")}),
        ):
            with self.app.test_client() as client:
                response = client.post("/start")
                raw = response.get_data()

        parts = raw.split(b"\n\n")
        data_parts = [p for p in parts if p.startswith(b"data: ")]
        flush_parts = [p for p in parts if p == b""]
        self.assertEqual(len(data_parts), 2)
        self.assertGreaterEqual(len(flush_parts), 1)


class TestStage2Man(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        choose_mod = MagicMock()
        validate_mod = MagicMock()
        save_mod = MagicMock()
        sys.modules["app.stage_2.choose_a_topic_to_continue_with.choose"] = choose_mod
        sys.modules["app.stage_2.validate_topics_by_removing_duplicates.validate"] = validate_mod
        sys.modules["app.stage_2.save_choosen_topic_in_used_topics.save"] = save_mod

        stage_2_path = APP / "stage_2" / "stage_2_man.py"
        spec = importlib.util.spec_from_file_location(
            "app.stage_2.stage_2_man",
            stage_2_path,
        )
        stage_2_man = importlib.util.module_from_spec(spec)
        sys.modules["app.stage_2.stage_2_man"] = stage_2_man
        spec.loader.exec_module(stage_2_man)

        cls._stage_2_fn = stage_2_man.start_stage_2
        cls.mock_validate = validate_mod.validate_topic
        cls.mock_choose = choose_mod.choose_single_topic
        cls.mock_save = save_mod.save_choosen_topic

    def setUp(self):
        self.mock_validate.reset_mock()
        self.mock_choose.reset_mock()
        self.mock_save.reset_mock()

    def _call_stage_2(self, topics):
        return type(self)._stage_2_fn(topics)

    def test_validate_error_returns_none(self):
        self.mock_validate.return_value = {"error": ValueError("bad topics")}
        result = self._call_stage_2([{"topic": "x"}])
        self.assertIsNone(result)
        self.mock_choose.assert_not_called()
        self.mock_save.assert_not_called()

    def test_choose_error_returns_none(self):
        self.mock_validate.return_value = [{"topic": "x"}]
        self.mock_choose.return_value = {"error": RuntimeError("model failed")}
        result = self._call_stage_2([{"topic": "x"}])
        self.assertIsNone(result)
        self.mock_choose.assert_called_once()
        self.mock_save.assert_not_called()

    def test_choose_none_returns_none(self):
        self.mock_validate.return_value = [{"topic": "x"}]
        self.mock_choose.return_value = None
        result = self._call_stage_2([{"topic": "x"}])
        self.assertIsNone(result)
        self.mock_save.assert_not_called()

    def test_save_error_returns_none(self):
        topics = [{"topic": "x"}]
        self.mock_validate.return_value = topics
        self.mock_choose.return_value = 0
        self.mock_save.return_value = {"error": OSError("write failed")}
        result = self._call_stage_2(topics)
        self.assertIsNone(result)
        self.mock_choose.assert_called_once_with(topics)

    def test_success_calls_choose_once(self):
        topics = [{"topic": "x"}, {"topic": "y"}]
        self.mock_validate.return_value = topics
        self.mock_choose.return_value = 1
        self.mock_save.return_value = None
        result = self._call_stage_2(topics)
        self.assertEqual(result, 1)
        self.mock_choose.assert_called_once_with(topics)
        self.mock_save.assert_called_once_with(topics[1])


if __name__ == "__main__":
    unittest.main()
