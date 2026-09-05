"""Exercise Streamlit interactions using isolated storage and no API requests."""

from __future__ import annotations

import os
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from streamlit.testing.v1 import AppTest
from test_core import make_bundle

import core


class AppTestCase(unittest.TestCase):
    def setUp(self) -> None:
        database = Path(__file__).parent / f".test-{uuid4().hex}.db"
        for path in (database, Path(f"{database}-wal"), Path(f"{database}-shm")):
            self.addCleanup(path.unlink, missing_ok=True)
        for name, value in {
            "DATABASE_URL": "",
            "DATABASE_FILE": str(database),
            "TRACKER_FILE": str(database.with_suffix(".csv")),
            "_initialized_target": None,
        }.items():
            patcher = patch.object(core, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        environment = patch.dict(os.environ, {"OPENAI_API_KEY": ""})
        environment.start()
        self.addCleanup(environment.stop)
        self.app = AppTest.from_file(
            str(Path(__file__).parents[1] / "app.py"), default_timeout=15
        )

    def save_sample(self) -> str:
        return core.save_application(
            company="Acme",
            role="Engineer",
            job_text="Build Python services.",
            bundle=make_bundle(),
            model="test-model",
            usage={},
        )

    def test_clearing_api_key_removes_session_credential(self) -> None:
        self.app.run()
        key_input = next(item for item in self.app.text_input if item.label == "OpenAI API key")
        key_input.set_value("test-key").run()
        self.assertEqual(self.app.session_state["api_key"], "test-key")
        key_input = next(item for item in self.app.text_input if item.label == "OpenAI API key")
        key_input.set_value("").run()
        self.assertNotIn("api_key", self.app.session_state)
        self.assertFalse(self.app.exception)

    def test_status_save_refreshes_both_views_and_dashboard(self) -> None:
        application_id = self.save_sample()
        self.app.session_state["current_result"] = core.get_application(application_id)
        self.app.run()
        self.app.selectbox(key=f"library_status_{application_id}").select("applied")
        self.app.button(key=f"library_save_status_{application_id}").click().run()
        self.assertFalse(self.app.exception)
        self.assertEqual(core.get_application(application_id)["status"], "applied")
        self.assertEqual(self.app.selectbox(key=f"new_status_{application_id}").value, "applied")
        applied_metric = next(item for item in self.app.metric if item.label == "Applied")
        self.assertEqual(applied_metric.value, "1")

    def test_letter_save_refreshes_other_view_and_preserves_unsaved_edits_on_rerun(self) -> None:
        application_id = self.save_sample()
        self.app.session_state["current_result"] = core.get_application(application_id)
        self.app.run()
        letter = "Dear team,\n\nI build Python services.\n\nRegards, Candidate"
        library_key = f"library_letter_{application_id}"
        self.app.text_area(key=library_key).set_value(letter).run()
        self.assertEqual(self.app.text_area(key=library_key).value, letter)
        self.app.button(key=f"library_save_letter_{application_id}").click().run()
        self.assertFalse(self.app.exception)
        self.assertEqual(self.app.text_area(key=f"new_letter_{application_id}").value, letter)
        self.assertEqual(core.get_application(application_id)["cover_letter"], letter)

    def test_database_failure_is_displayed_without_crashing(self) -> None:
        self.save_sample()
        with patch.object(core, "get_application", side_effect=core.AssistantError("Database offline")):
            self.app.run()
        self.assertFalse(self.app.exception)
        self.assertTrue(any(item.value == "Database offline" for item in self.app.error))


if __name__ == "__main__":
    unittest.main()
