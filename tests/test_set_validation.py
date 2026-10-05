from pathlib import Path
import sys
import tempfile
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from application.song_service import SongService
from core.storage import StorageManager
from models.assets import AssetType


class SetValidationTest(unittest.TestCase):
    def test_sample_fingerprint_tracks_linked_spec_content_without_review_metadata(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            storage = StorageManager(Path(temp_dir))
            service = SongService(storage)
            service.bootstrap()
            set_id = self.create_valid_set(service).name
            project = storage.create_song_project("Produccion", f"set:{set_id}")
            song_id = str(project["id"])
            storage.upsert_song_spec(song_id, {"bpm": 100, "provider": "local"}, True, [])
            fingerprint = storage.set_generation_fingerprint(set_id)
            storage.upsert_song_spec(song_id, {"bpm": 100, "provider": "local"}, True, [],
                                     user_confirmation_status="confirmed")
            self.assertEqual(storage.set_generation_fingerprint(set_id), fingerprint)
            unrelated = storage.create_song_project("Otra idea", "set:other")
            storage.upsert_song_spec(str(unrelated["id"]), {"bpm": 140}, True, [])
            self.assertEqual(storage.set_generation_fingerprint(set_id), fingerprint)
            storage.upsert_song_spec(song_id, {"bpm": 100, "provider": "different"}, True, [])
            self.assertNotEqual(storage.set_generation_fingerprint(set_id), fingerprint)

    def test_sample_fingerprint_ignores_phase_metadata_but_tracks_music(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            storage = StorageManager(Path(temp_dir))
            service = SongService(storage)
            service.bootstrap()
            set_id = self.create_valid_set(service).name
            payload = {"musicPlan": {"bpm": 100, "key": "C"}}
            storage.save_project_phase_data(set_id, "music-plan", payload, "pending")
            fingerprint = storage.set_generation_fingerprint(set_id)
            storage.save_project_phase_data(set_id, "music-plan", payload, "completed", change_source="AI")
            storage.save_project_phase_data(set_id, "production", {
                "production": {"productionProjectId": "song1", "productionGlobalStatus": "ready"}}, "completed")
            self.assertEqual(storage.set_generation_fingerprint(set_id), fingerprint)
            storage.save_project_phase_data(set_id, "music-plan", {
                "musicPlan": {"bpm": 120, "key": "C"}}, "completed")
            self.assertNotEqual(storage.set_generation_fingerprint(set_id), fingerprint)

    def create_valid_set(self, service: SongService, name: str = "Prueba") -> Path:
        instrumental = service.create_instrumental({})["id"]
        melody = service.create_melody({})["id"]
        lyrics = service.create_lyrics({})["id"]
        return service.set_builder.create_from_asset_ids(instrumental, melody, lyrics, name, "")

    def test_set_rejects_missing_or_wrong_type_drafts_before_persisting(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            storage = StorageManager(Path(temp_dir))
            service = SongService(storage)
            service.bootstrap()
            instrumental = service.create_instrumental({})["id"]
            melody = service.create_melody({})["id"]
            lyrics = service.create_lyrics({})["id"]

            for bad_instrumental in ("missing", lyrics):
                with self.assertRaisesRegex(ValueError, "instrumental"):
                    service.set_builder.create_from_asset_ids(
                        bad_instrumental, melody, lyrics, "Prueba", "",
                    )
            self.assertEqual(storage.list_indexed_sets(), [])

            intent_path = storage.get_asset_draft_dir(AssetType.INSTRUMENTAL, instrumental) / "intent.json"
            intent_snapshot = intent_path.read_text(encoding="utf-8")
            intent_path.unlink()
            with self.assertRaisesRegex(ValueError, "incompleto"):
                service.set_builder.create_from_asset_ids(instrumental, melody, lyrics, "Prueba", "")
            intent_path.write_text(intent_snapshot, encoding="utf-8")

            set_path = service.set_builder.create_from_asset_ids(
                instrumental, melody, lyrics, "Prueba", "",
            )
            self.assertTrue((set_path / "set.json").exists())

    def test_selected_assets_and_request_id_are_persisted_once(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            storage = StorageManager(Path(temp_dir))
            service = SongService(storage)
            service.bootstrap()
            for _ in range(2):
                service.create_instrumental({})
                service.create_melody({})
                service.create_lyrics({})
            chosen = {kind: storage.list_asset_drafts_by_type(kind)[1]["asset_id"] for kind in AssetType}
            payload = {
                "project_name": "Seleccionado", "description": "Segunda terna", "request_id": "same-click",
                "instrumental_id": chosen[AssetType.INSTRUMENTAL],
                "melody_id": chosen[AssetType.MELODY],
                "lyrics_id": chosen[AssetType.LYRICS],
            }
            first = service.create_set(payload)
            second = service.create_set(payload)
            self.assertEqual(first["id"], second["id"])
            self.assertEqual(len(storage.list_indexed_sets()), 1)
            persisted = storage.get_indexed_set(first["id"])
            for kind in AssetType:
                self.assertEqual(persisted[f"{kind.value}_id"], chosen[kind])
            self.assertEqual(storage.read_json(Path(first["path"]) / "set.json")["lyrics_id"], chosen[AssetType.LYRICS])
            with self.assertRaisesRegex(ValueError, "ya se uso"):
                service.create_set({**payload, "project_name": "Otro"})

    def test_invalid_bpm_does_not_replace_saved_phase(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            storage = StorageManager(Path(temp_dir))
            service = SongService(storage)
            service.bootstrap()
            set_id = self.create_valid_set(service).name
            service.save_project_phase_data(set_id, "intent", {"data": {"intent": {"bpm": 77}}})
            for value in (0, -20, 241, "abc", "", None):
                with self.assertRaisesRegex(ValueError, "BPM"):
                    service.save_project_phase_data(set_id, "intent", {"data": {"intent": {"bpm": value}}})
                self.assertEqual(service.get_project(set_id)["phase_data"]["intent"]["data"]["intent"]["bpm"], 77)
            service.save_project_phase_data(set_id, "music-plan", {"data": {"musicPlan": {"bpm": 48}}})
            service.save_project_phase_data(set_id, "music-plan", {"data": {"musicPlan": {"bpm": 240}}})

    def test_explicit_lyric_content_is_kept_in_separate_draft(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            storage = StorageManager(Path(temp_dir))
            service = SongService(storage)
            service.bootstrap()
            content = "## Verso\nCancion propia para {name}.\n"
            asset_id = service.create_lyrics({"theme": "cancion propia", "content": content})["id"]
            draft = storage.get_asset_draft_detail(asset_id)
            self.assertEqual(draft["content"], content)
            self.assertTrue((Path(draft["path"]) / "manifest.json").is_file())
            self.assertTrue((Path(draft["path"]) / "intent.json").is_file())

    def test_sample_and_full_song_require_a_valid_current_set(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            storage = StorageManager(Path(temp_dir))
            service = SongService(storage)
            service.bootstrap()
            instrumental = service.create_instrumental({})["id"]
            melody = service.create_melody({})["id"]
            lyrics = service.create_lyrics({})["id"]
            set_path = service.set_builder.create_from_asset_ids(
                instrumental, melody, lyrics, "Prueba", "",
            )

            metadata = storage.get_asset_draft_dir(AssetType.INSTRUMENTAL, instrumental) / "metadata.json"
            metadata.unlink()
            with self.assertRaisesRegex(ValueError, "instrumental"):
                service.sample_builder.create_from_latest_set()
            self.assertEqual(storage.list_samples(), [])

            # Restore the original draft so this same set can advance to a sample.
            metadata.write_text('{"asset_id": "' + instrumental + '", "asset_type": "instrumental"}', encoding="utf-8")
            (set_path / "set.json").unlink()
            service.sample_builder.create_from_latest_set()
            storage.set_repository.delete_set(set_path.name)
            with self.assertRaisesRegex(ValueError, "set valido"):
                service.full_song_builder.create_from_latest_sample()
            self.assertEqual(storage.list_songs(), [])

    def test_legacy_sample_and_song_are_restored_from_sqlite(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            root = Path(temp_dir)
            storage = StorageManager(root)
            service = SongService(storage)
            service.bootstrap()
            set_path = self.create_valid_set(service)
            sample_path = service.sample_builder.create_from_latest_set()
            storage.approve_sample(set_path.name, sample_path.name)
            song_path = service.full_song_builder.create_from_latest_sample()
            sample_id = sample_path.name
            song_id = song_path.name

            (sample_path / "sample.json").unlink()
            (song_path / "song.json").unlink()

            restarted_storage = StorageManager(root)
            SongService(restarted_storage).bootstrap()
            restored_sample = restarted_storage.get_latest_sample()
            restored_song = restarted_storage.get_latest_song()

            self.assertEqual(restored_sample["sample_id"], sample_id)
            self.assertEqual(restored_song["song_id"], song_id)
            self.assertEqual(restored_song["set_id"], set_path.name)
            self.assertTrue((sample_path / "sample.json").exists())
            self.assertTrue((song_path / "song.json").exists())

            deleted = restarted_storage.delete_indexed_project(set_path.name)
            self.assertEqual(deleted["legacy_samples_deleted"], [sample_id])
            self.assertEqual(deleted["legacy_songs_deleted"], [song_id])
            self.assertFalse(sample_path.exists())
            self.assertFalse(song_path.exists())

    def test_full_song_requires_approved_current_sample_from_active_set(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            storage = StorageManager(Path(temp_dir))
            service = SongService(storage)
            service.bootstrap()
            set_a = self.create_valid_set(service, "Proyecto A")
            set_b = self.create_valid_set(service, "Proyecto B")

            sample_a = service.sample_builder.create_for_set(set_a.name)
            with self.assertRaisesRegex(ValueError, "aprueba el sample"):
                service.full_song_builder.create_for_set(set_a.name, sample_a.name)

            approved = service.approve_sample(set_a.name, sample_a.name)
            self.assertEqual(approved["approval_status"], "approved")
            with self.assertRaisesRegex(ValueError, "set activo"):
                service.approve_sample(set_b.name, sample_a.name)
            with self.assertRaisesRegex(ValueError, "sample del set activo"):
                service.full_song_builder.create_for_set(set_b.name, sample_a.name)

            lyrics_id = str(storage.get_indexed_set(set_a.name)["lyrics_id"])
            lyrics_path = storage.get_asset_draft_dir(AssetType.LYRICS, lyrics_id) / "lyrics.md"
            lyrics_path.write_text(lyrics_path.read_text(encoding="utf-8") + "\nCambio creativo.\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "desactualizado"):
                service.full_song_builder.create_for_set(set_a.name, sample_a.name)

            fresh_sample = service.sample_builder.create_for_set(set_a.name)
            service.approve_sample(set_a.name, fresh_sample.name)
            song_path = service.full_song_builder.create_for_set(set_a.name, fresh_sample.name)
            song = storage.get_latest_song()
            self.assertEqual(song["set_id"], set_a.name)
            self.assertEqual(song["sample_id"], fresh_sample.name)
            self.assertTrue((song_path / "song.json").exists())

    def test_legacy_json_migration_is_idempotent_and_does_not_overwrite_sqlite(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            root = Path(temp_dir)
            storage = StorageManager(root)
            service = SongService(storage)
            service.bootstrap()
            set_path = self.create_valid_set(service)
            sample_dir = root / "samples" / "sample-legacy"
            sample_dir.mkdir(parents=True)
            sample_json = sample_dir / "sample.json"
            storage.write_json(
                sample_json,
                {
                    "sample_id": "sample-legacy",
                    "set_id": set_path.name,
                    "provider": "mock-local",
                    "status": "original",
                },
            )

            first = storage.sync_legacy_workflow_to_sqlite()
            storage.write_json(sample_json, {"sample_id": "sample-legacy", "set_id": set_path.name, "status": "stale"})
            second = storage.sync_legacy_workflow_to_sqlite()

            persisted = storage.legacy_song_repository.get_sample("sample-legacy")
            self.assertEqual(first["samples"], ["sample-legacy"])
            self.assertEqual(second["samples"], [])
            self.assertEqual(persisted["status"], "original")

    def test_project_download_never_uses_another_projects_export(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            root = Path(temp_dir)
            storage = StorageManager(root)
            service = SongService(storage)
            service.bootstrap()
            set_a = self.create_valid_set(service, "Proyecto A")
            set_b = self.create_valid_set(service, "Proyecto B")

            for set_path, marker in ((set_a, b"audio-a"), (set_b, b"audio-b")):
                sample_id = f"sample-{set_path.name}"
                song_id = f"song-{set_path.name}"
                sample_json = root / "samples" / sample_id / "sample.json"
                song_dir = root / "songs" / song_id
                storage.save_legacy_sample(
                    {"sample_id": sample_id, "set_id": set_path.name, "status": "ready", "provider": "test"},
                    sample_json,
                )
                storage.save_legacy_song(
                    {
                        "song_id": song_id,
                        "sample_id": sample_id,
                        "set_id": set_path.name,
                        "status": "ready",
                        "provider": "test",
                        "exports_dir": str(song_dir / "exports"),
                        "stems_dir": str(song_dir / "stems"),
                    },
                    song_dir / "song.json",
                )
                exports = song_dir / "exports"
                exports.mkdir(parents=True, exist_ok=True)
                (exports / "final_mix.mp3").write_bytes(marker)
                storage.write_json(
                    exports / "local_final_manifest.json",
                    {"song_id": song_id, "set_id": set_path.name},
                )

            path_a, name_a = service.project_audio_export_file(set_a.name, "mp3")
            self.assertEqual(path_a.read_bytes(), b"audio-a")
            self.assertEqual(name_a, "Proyecto_A.mp3")

            path_a.unlink()
            with self.assertRaisesRegex(ValueError, "proyecto activo"):
                service.project_audio_export_file(set_a.name, "mp3")
            path_b, _name_b = service.project_audio_export_file(set_b.name, "mp3")
            self.assertEqual(path_b.read_bytes(), b"audio-b")


if __name__ == "__main__":
    unittest.main()
