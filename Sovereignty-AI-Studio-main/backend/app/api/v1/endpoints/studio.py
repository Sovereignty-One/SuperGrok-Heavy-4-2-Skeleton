"""API endpoints for voice interaction, avatar, media, music, syntax,
dashboard builder, and BLE LiDAR EEG services."""
from fastapi import APIRouter

router = APIRouter()


# ── Voice Interaction ────────────────────────────────────────────────
@router.get("/voice/status")
async def voice_status():
    from app.services.voice_interaction_service import voice_interaction_service
    return voice_interaction_service.get_status()


@router.post("/voice/session")
async def create_voice_session(user_id: str = "default", voice_model: str = "en_US-lessac-medium"):
    from app.services.voice_interaction_service import voice_interaction_service
    session = voice_interaction_service.create_session(user_id, voice_model)
    return {
        "session_id": session.session_id,
        "user_id": session.user_id,
        "state": session.state.value,
    }


@router.post("/voice/interact")
async def voice_interact(session_id: str, text: str):
    from app.services.voice_interaction_service import voice_interaction_service
    return voice_interaction_service.process_text_input(session_id, text)


@router.get("/voice/voices")
async def list_voices():
    from app.services.voice_interaction_service import voice_interaction_service
    return voice_interaction_service.get_available_voices()


# ── Avatar Companion ─────────────────────────────────────────────────
@router.get("/avatar/status")
async def avatar_status():
    from app.services.avatar_companion_service import avatar_companion_service
    return avatar_companion_service.get_status()


@router.post("/avatar/create")
async def create_avatar(
    user_id: str = "default",
    name: str = "Ara",
    style: str = "minimal",
):
    from app.services.avatar_companion_service import avatar_companion_service
    return avatar_companion_service.create_avatar(user_id, name=name, style=style)


@router.post("/avatar/interact")
async def avatar_interact(avatar_id: str, message: str):
    from app.services.avatar_companion_service import avatar_companion_service
    return avatar_companion_service.interact(avatar_id, message)


# ── Media Generator ──────────────────────────────────────────────────
@router.get("/media/status")
async def media_status():
    from app.services.media_generator_service import media_generator_service
    return media_generator_service.get_status()


@router.post("/media/generate")
async def generate_media(
    user_id: str = "default",
    media_type: str = "image",
    prompt: str = "",
):
    from app.services.media_generator_service import media_generator_service
    return media_generator_service.generate(user_id, media_type, prompt)


@router.get("/media/job/{job_id}")
async def get_media_job(job_id: str):
    from app.services.media_generator_service import media_generator_service
    result = media_generator_service.get_job(job_id)
    if not result:
        return {"error": "Job not found"}
    return result


# ── Music Generator ──────────────────────────────────────────────────
@router.get("/music/status")
async def music_status():
    from app.services.music_generator_service import music_generator_service
    return music_generator_service.get_status()


@router.post("/music/compose")
async def compose_music(
    user_id: str = "default",
    prompt: str = "",
    genre: str = "ambient",
    duration_seconds: int = 30,
    bpm: int = 120,
):
    from app.services.music_generator_service import music_generator_service
    return music_generator_service.compose(
        user_id, prompt, genre, duration_seconds, bpm
    )


# ── Syntax Checker ───────────────────────────────────────────────────
@router.get("/syntax/status")
async def syntax_status():
    from app.services.syntax_checker_service import syntax_checker
    return syntax_checker.get_status()


@router.post("/syntax/check")
async def check_syntax(source: str, file_path: str = "<input>"):
    from app.services.syntax_checker_service import syntax_checker
    return syntax_checker.check_python(source, file_path)


# ── Dashboard Builder ────────────────────────────────────────────────
@router.get("/dashboard/status")
async def dashboard_status():
    from app.services.dashboard_builder_service import dashboard_builder_service
    return dashboard_builder_service.get_status()


@router.post("/dashboard/project")
async def create_dashboard_project(
    user_id: str = "default",
    name: str = "",
    project_type: str = "web_app",
):
    from app.services.dashboard_builder_service import dashboard_builder_service
    return dashboard_builder_service.create_project(user_id, name, project_type)


@router.post("/dashboard/build/{project_id}")
async def trigger_build(project_id: str):
    from app.services.dashboard_builder_service import dashboard_builder_service
    return dashboard_builder_service.trigger_build(project_id)


# ── BLE LiDAR EEG ────────────────────────────────────────────────────
@router.get("/ble-eeg/status")
async def ble_eeg_status():
    from app.services.ble_lidar_eeg_service import ble_lidar_eeg_service
    return ble_lidar_eeg_service.get_status()


@router.post("/ble-eeg/scan")
async def scan_ble_devices():
    from app.services.ble_lidar_eeg_service import ble_lidar_eeg_service
    return ble_lidar_eeg_service.scan_devices()


@router.post("/ble-eeg/connect/{device_id}")
async def connect_ble_device(device_id: str):
    from app.services.ble_lidar_eeg_service import ble_lidar_eeg_service
    return ble_lidar_eeg_service.connect_device(device_id)


@router.post("/ble-eeg/stream/{device_id}")
async def start_eeg_stream(device_id: str):
    from app.services.ble_lidar_eeg_service import ble_lidar_eeg_service
    return ble_lidar_eeg_service.start_eeg_stream(device_id)


@router.get("/ble-eeg/reading/{device_id}")
async def get_eeg_reading(device_id: str):
    from app.services.ble_lidar_eeg_service import ble_lidar_eeg_service
    return ble_lidar_eeg_service.get_eeg_reading(device_id)
