"""Tests for the new Sovereignty AI Studio services.

Covers voice interaction, avatar companion, media generator, music generator,
syntax checker, dashboard builder, and BLE LiDAR EEG services.
"""
import pytest

# ── Voice Interaction Service ────────────────────────────────────────

from backend.app.services.voice_interaction_service import (
    VoiceInteractionService,
    VoiceState,
)


class TestVoiceInteractionService:
    def setup_method(self):
        self.svc = VoiceInteractionService()

    def test_create_session(self):
        session = self.svc.create_session("user1")
        assert session.session_id
        assert session.user_id == "user1"
        assert session.state == VoiceState.IDLE

    def test_get_session(self):
        session = self.svc.create_session("user1")
        found = self.svc.get_session(session.session_id)
        assert found is not None
        assert found.session_id == session.session_id

    def test_end_session(self):
        session = self.svc.create_session("user1")
        assert self.svc.end_session(session.session_id) is True
        assert self.svc.get_session(session.session_id) is None

    def test_process_text_input(self):
        session = self.svc.create_session("user1")
        result = self.svc.process_text_input(session.session_id, "hello")
        assert "response_text" in result
        assert result["session_id"] == session.session_id

    def test_process_text_input_invalid_session(self):
        result = self.svc.process_text_input("nonexistent", "hello")
        assert "error" in result

    def test_available_voices(self):
        voices = self.svc.get_available_voices()
        assert len(voices) > 0
        assert all("id" in v for v in voices)

    def test_status(self):
        status = self.svc.get_status()
        assert status["service"] == "voice_interaction"
        assert status["status"] == "online"


# ── Avatar Companion Service ─────────────────────────────────────────

from backend.app.services.avatar_companion_service import (
    AvatarCompanionService,
)


class TestAvatarCompanionService:
    def setup_method(self):
        self.svc = AvatarCompanionService()

    def test_create_avatar(self):
        result = self.svc.create_avatar("user1", name="Aria")
        assert result["name"] == "Aria"
        assert result["user_id"] == "user1"
        assert result["style"] == "minimal"

    def test_get_avatar(self):
        created = self.svc.create_avatar("user1")
        found = self.svc.get_avatar(created["avatar_id"])
        assert found is not None
        assert found["avatar_id"] == created["avatar_id"]

    def test_interact(self):
        created = self.svc.create_avatar("user1")
        result = self.svc.interact(created["avatar_id"], "hello")
        assert "response" in result
        assert result["interaction_count"] == 1

    def test_interact_nonexistent(self):
        result = self.svc.interact("fake-id", "hello")
        assert "error" in result

    def test_delete_avatar(self):
        created = self.svc.create_avatar("user1")
        assert self.svc.delete_avatar(created["avatar_id"]) is True
        assert self.svc.get_avatar(created["avatar_id"]) is None

    def test_status(self):
        status = self.svc.get_status()
        assert status["service"] == "avatar_companion"


# ── Media Generator Service ──────────────────────────────────────────

from backend.app.services.media_generator_service import (
    MediaGeneratorService,
)


class TestMediaGeneratorService:
    def setup_method(self):
        self.svc = MediaGeneratorService()

    def test_generate_image(self):
        result = self.svc.generate("user1", "image", "a sunset")
        assert result["media_type"] == "image"
        assert result["status"] == "completed"
        assert result["result_path"] is not None

    def test_generate_video(self):
        result = self.svc.generate("user1", "video", "waves crashing")
        assert result["media_type"] == "video"
        assert result["status"] == "completed"

    def test_generate_audio(self):
        result = self.svc.generate("user1", "audio", "rain sounds")
        assert result["media_type"] == "audio"
        assert result["status"] == "completed"

    def test_get_job(self):
        result = self.svc.generate("user1", "image", "test")
        found = self.svc.get_job(result["job_id"])
        assert found is not None

    def test_list_jobs(self):
        self.svc.generate("user1", "image", "test1")
        self.svc.generate("user2", "video", "test2")
        all_jobs = self.svc.list_jobs()
        assert len(all_jobs) == 2
        user1_jobs = self.svc.list_jobs(user_id="user1")
        assert len(user1_jobs) == 1

    def test_status(self):
        status = self.svc.get_status()
        assert status["service"] == "media_generator"


# ── Music Generator Service ──────────────────────────────────────────

from backend.app.services.music_generator_service import (
    MusicGeneratorService,
)


class TestMusicGeneratorService:
    def setup_method(self):
        self.svc = MusicGeneratorService()

    def test_compose(self):
        result = self.svc.compose("user1", "calm piano", genre="classical", bpm=90)
        assert result["genre"] == "classical"
        assert result["bpm"] == 90
        assert result["status"] == "completed"

    def test_compose_clamped_bpm(self):
        result = self.svc.compose("user1", "fast", bpm=999)
        assert result["bpm"] == 240

    def test_compose_clamped_duration(self):
        result = self.svc.compose("user1", "long", duration_seconds=9999)
        assert result["duration_seconds"] == 300

    def test_get_job(self):
        result = self.svc.compose("user1", "test")
        found = self.svc.get_job(result["job_id"])
        assert found is not None

    def test_status(self):
        status = self.svc.get_status()
        assert status["service"] == "music_generator"


# ── Syntax Checker Service ───────────────────────────────────────────

from backend.app.services.syntax_checker_service import (
    SyntaxCheckerService,
)


class TestSyntaxCheckerService:
    def setup_method(self):
        self.svc = SyntaxCheckerService()

    def test_valid_python(self):
        report = self.svc.check_python("x = 1\nprint(x)\n")
        assert report["success"] is True
        assert report["errors"] == 0

    def test_syntax_error(self):
        report = self.svc.check_python("def foo(\n")
        assert report["success"] is False
        assert report["errors"] > 0

    def test_trailing_whitespace(self):
        report = self.svc.check_python("x = 1   \n")
        info_issues = [i for i in report["issues"] if i["severity"] == "info"]
        assert len(info_issues) > 0

    def test_colour_output_no_issues(self):
        report = self.svc.check_python("x = 1\n")
        coloured = self.svc.format_coloured(report)
        assert "✓" in coloured

    def test_colour_output_with_error(self):
        report = self.svc.check_python("def foo(\n")
        coloured = self.svc.format_coloured(report)
        assert "[ERROR]" in coloured

    def test_status(self):
        status = self.svc.get_status()
        assert status["service"] == "syntax_checker"
        assert status["colour_coded"] is True


# ── Dashboard Builder Service ────────────────────────────────────────

from backend.app.services.dashboard_builder_service import (
    DashboardBuilderService,
)


class TestDashboardBuilderService:
    def setup_method(self):
        self.svc = DashboardBuilderService()

    def test_create_project(self):
        result = self.svc.create_project("user1", "My Game", "game")
        assert result["name"] == "My Game"
        assert result["project_type"] == "game"
        assert result["task_count"] > 0

    def test_get_project(self):
        created = self.svc.create_project("user1", "Test")
        found = self.svc.get_project(created["project_id"])
        assert found is not None

    def test_add_task(self):
        project = self.svc.create_project("user1", "Test")
        task = self.svc.add_task(project["project_id"], "New task")
        assert task is not None
        assert task["title"] == "New task"

    def test_trigger_build(self):
        project = self.svc.create_project("user1", "Test")
        result = self.svc.trigger_build(project["project_id"])
        assert result["build_status"] == "success"

    def test_trigger_build_nonexistent(self):
        result = self.svc.trigger_build("fake-id")
        assert "error" in result

    def test_delete_project(self):
        project = self.svc.create_project("user1", "Test")
        assert self.svc.delete_project(project["project_id"]) is True

    def test_status(self):
        status = self.svc.get_status()
        assert status["service"] == "dashboard_builder"


# ── BLE LiDAR EEG Service ───────────────────────────────────────────

from backend.app.services.ble_lidar_eeg_service import (
    BLELidarEEGService,
)


class TestBLELidarEEGService:
    def setup_method(self):
        self.svc = BLELidarEEGService()

    def test_scan_devices(self):
        devices = self.svc.scan_devices()
        assert len(devices) >= 2
        types = {d["device_type"] for d in devices}
        assert "eeg_headset" in types
        assert "lidar_sensor" in types

    def test_connect_device(self):
        devices = self.svc.scan_devices()
        result = self.svc.connect_device(devices[0]["device_id"])
        assert result["state"] == "connected"

    def test_connect_nonexistent(self):
        result = self.svc.connect_device("fake-id")
        assert "error" in result

    def test_eeg_stream(self):
        devices = self.svc.scan_devices()
        eeg_dev = next(d for d in devices if d["device_type"] == "eeg_headset")
        self.svc.connect_device(eeg_dev["device_id"])
        result = self.svc.start_eeg_stream(eeg_dev["device_id"])
        assert result["state"] == "streaming"

    def test_eeg_reading(self):
        devices = self.svc.scan_devices()
        eeg_dev = next(d for d in devices if d["device_type"] == "eeg_headset")
        self.svc.connect_device(eeg_dev["device_id"])
        self.svc.start_eeg_stream(eeg_dev["device_id"])
        reading = self.svc.get_eeg_reading(eeg_dev["device_id"])
        assert "band_powers" in reading
        assert "alpha" in reading["band_powers"]

    def test_lidar_frame(self):
        devices = self.svc.scan_devices()
        lidar_dev = next(d for d in devices if d["device_type"] == "lidar_sensor")
        result = self.svc.get_lidar_frame(lidar_dev["device_id"])
        assert "point_count" in result
        assert result["point_count"] > 0

    def test_disconnect(self):
        devices = self.svc.scan_devices()
        self.svc.connect_device(devices[0]["device_id"])
        result = self.svc.disconnect_device(devices[0]["device_id"])
        assert result["state"] == "disconnected"

    def test_status(self):
        status = self.svc.get_status()
        assert status["service"] == "ble_lidar_eeg"
        assert status["status"] == "online"
