import sys
import unittest
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from application.candidate_correction import ProposeCandidateCorrection


class CandidateCorrectionTest(unittest.TestCase):
    def setUp(self):
        self.store, self.jobs, self.read, self.audio = Mock(), Mock(), Mock(), Mock()
        self.review = {"decision": "changes_requested", "inputs_current": True,
            "reviewed_at": "date", "notes": "Corregir coro", "criteria": {"lyrics": "needs_changes"},
            "artifact_id": "a", "audio_sha256": "hash", "plan_id": "p", "spec_revision_id": "r"}
        self.read.return_value = {"review": self.review}
        self.jobs.get.return_value = {"result": {"fidelity_report": {"checks": [
            {"id": "duration", "method": "wav_frames_sample_rate", "observed": 30}]}}}
        self.action = ProposeCandidateCorrection(self.store, self.jobs, self.read, self.audio)

    def test_scopes_preserve_provenance_without_executing_or_approving(self):
        for scope, mode in (("segment", "repaint"), ("style", "cover"), ("reinterpret", "text2music")):
            result = self.action.execute("s", "t", {"reviewed_at": "date", "scope": scope, "start": 5, "end": 10})
            p = result["proposal"]
            self.assertEqual(p["proposed_parameters"]["task_type"], mode)
            self.assertEqual(p["notes"], "Corregir coro")
            self.assertEqual(p["plan_id"], "p")
            self.assertFalse(p["ready_for_execution"])
            self.assertEqual(p["source_artifact_id"], None if scope == "reinterpret" else "a")
        self.jobs.start.assert_not_called()
        self.store.save_song_spec.assert_not_called()
        self.assertNotIn("scope", self.review)

    def test_invalid_or_unmeasured_intervals_cannot_be_saved(self):
        for start, end in ((True, 10), (0, float("nan")), (-1, 10), (10, 10), (0, 31), (None, 10)):
            with self.assertRaises(ValueError):
                self.action.execute("s", "t", {"reviewed_at": "date", "scope": "segment", "start": start, "end": end})
        self.jobs.get.return_value = {"result": {}}
        with self.assertRaises(ValueError):
            self.action.execute("s", "t", {"reviewed_at": "date", "scope": "segment", "start": 0, "end": 10})
        self.store.create_song_event.assert_not_called()

    def test_stale_accepted_or_changed_review_and_bad_source_are_rejected(self):
        for changes in ({"inputs_current": False}, {"decision": "accepted"}, {"reviewed_at": "new"}):
            self.read.return_value = {"review": {**self.review, **changes}}
            with self.assertRaises(ValueError):
                self.action.execute("s", "t", {"reviewed_at": "date", "scope": "style"})
        self.read.return_value = {"review": self.review}
        self.audio.side_effect = ValueError("changed")
        with self.assertRaises(ValueError):
            self.action.execute("s", "t", {"reviewed_at": "date", "scope": "style"})
        self.store.create_song_event.assert_not_called()

    def test_owner_and_scope_failures_do_not_persist(self):
        for scope in (None, [], "lego"):
            with self.assertRaises(ValueError):
                self.action.execute("s", "t", {"reviewed_at": "date", "scope": scope})
        self.jobs.get.side_effect = ValueError("wrong owner")
        with self.assertRaises(ValueError):
            self.action.execute("other", "t", {"reviewed_at": "date", "scope": "style"})
        self.read.assert_called_with("s", "t")
        self.store.create_song_event.assert_not_called()

    def test_recovery_derives_currentness_without_rewriting_history(self):
        p = self.action.execute("s", "t", {"reviewed_at": "date", "scope": "style"})["proposal"]
        self.store.reset_mock()
        self.store.list_song_project_events.return_value = [{"payload": {"candidate_correction": p}}]
        current = self.action.latest("s", "t")["proposal"]
        self.assertTrue(current["inputs_current"])
        self.assertFalse(current["ready_for_execution"])
        for changes in ({"reviewed_at": "new"}, {"inputs_current": False}, {"decision": "accepted"}, {"plan_id": "other"}):
            self.read.return_value = {"review": {**self.review, **changes}}
            self.assertFalse(self.action.latest("s", "t")["proposal"]["inputs_current"])
        self.assertNotIn("inputs_current", p)
        self.store.create_song_event.assert_not_called()

    def test_missing_or_replaced_audio_and_foreign_task_recovery(self):
        self.store.list_song_project_events.return_value = []
        self.assertIsNone(self.action.latest("s", "t")["proposal"])
        p = self.action.execute("s", "t", {"reviewed_at": "date", "scope": "style"})["proposal"]
        self.store.list_song_project_events.return_value = [{"payload": {"candidate_correction": p}}]
        self.audio.side_effect = OSError("missing file")
        result = self.action.latest("s", "t")["proposal"]
        self.assertFalse(result["inputs_current"])
        self.assertEqual(result["invalid_reason"], "missing file")
        self.jobs.get.side_effect = ValueError("wrong owner")
        with self.assertRaises(ValueError):
            self.action.latest("other", "t")

    def test_base_actions_require_explicit_tracks_and_matching_instruction(self):
        for scope, mode in (("add_track", "lego"), ("isolate_track", "extract"), ("arrangement", "complete")):
            result = self.action.execute("s", "t", {"reviewed_at": "date", "scope": scope,
                "target_tracks": ["guitar"], "instruction": "guitar"})["proposal"]
            self.assertEqual(result["proposed_parameters"]["task_type"], mode)
            self.assertEqual(result["proposed_parameters"]["ace_step_config"], "acestep-v15-base")
            self.assertEqual(result["source_artifact_id"], "a")
            self.assertFalse(result["ready_for_execution"])
        for tracks, instruction in (([], "guitar"), (["invented"], "invented"), (["guitar"], "drums"),
                                    (["guitar", "drums"], "guitar drums"), ([True], "guitar"), (["guitar"], None)):
            with self.assertRaises(ValueError):
                self.action.execute("s", "t", {"reviewed_at": "date", "scope": "add_track",
                    "target_tracks": tracks, "instruction": instruction})

    def test_sqlite_recovers_proposal_after_reopening_store(self):
        import tempfile
        from core.storage import StorageManager
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
            store = StorageManager(Path(folder))
            song = store.create_song_project("Correccion")["id"]
            action = ProposeCandidateCorrection(store, self.jobs, self.read, self.audio)
            saved = action.execute(song, "t", {"reviewed_at": "date", "scope": "style"})["proposal"]
            reopened = StorageManager(Path(folder))
            result = ProposeCandidateCorrection(reopened, self.jobs, self.read, self.audio).latest(song, "t")["proposal"]
            self.assertEqual(result["created_at"], saved["created_at"])
            self.assertTrue(result["inputs_current"])
            self.assertIsNone(ProposeCandidateCorrection(reopened, self.jobs, self.read, self.audio).latest(
                reopened.create_song_project("Otro")["id"], "t")["proposal"])
