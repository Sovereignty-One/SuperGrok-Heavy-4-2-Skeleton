import logging
import asyncio
import time
import uuid
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from collections import defaultdict

from subs2cia.Common import Common
from subs2cia.sources import AVSFile, Stream
from subs2cia.pickers import picker

try:
    import websockets
except ImportError:
    websockets = None

# ANSI color codes for color-coded progress bars
COLORS = {
    "in_progress": "\033[94m",  # Blue
    "completed": "\033[92m",    # Green
    "failed": "\033[91m",       # Red
    "reset": "\033[0m"          # Reset
}

PROGRESS_STATE_FILE = "progress_state.json"


def structured_log(logger: logging.Logger, level: str, message: str, **kwargs) -> None:
    log_entry = {
        "timestamp": time.time(),
        "uuid": str(uuid.uuid4()),
        "level": level.upper(),
        "message": message,
        **kwargs
    }
    logger.log(getattr(logging, level.upper(), logging.INFO), json.dumps(log_entry))


def save_progress_state(state: Dict[str, Any]) -> None:
    with open(PROGRESS_STATE_FILE, 'w') as f:
        json.dump(state, f)


def load_progress_state() -> Dict[str, Any]:
    if os.path.exists(PROGRESS_STATE_FILE):
        with open(PROGRESS_STATE_FILE, 'r') as f:
            return json.load(f)
    return {}


def make_progress_event(task: str, status: str, percent: int, file: Optional[str] = None,
                        error: Optional[str] = None, start_time: Optional[float] = None) -> Dict[str, Any]:
    now = time.time()
    elapsed = now - start_time if start_time else None
    eta = None
    if elapsed is not None and percent > 0:
        total_estimated = elapsed / (percent / 100)
        eta = max(0, total_estimated - elapsed)

    event = {
        "uuid": str(uuid.uuid4()),
        "timestamp": now,
        "task": task,
        "status": status,
        "percent": percent,
        "file": file,
        "error": error,
        "eta": eta
    }
    state = load_progress_state()
    state[task] = event
    save_progress_state(state)
    return event


async def render_progress(queue: asyncio.Queue) -> None:
    """Render multi-line, color-coded progress bars for parallel tasks."""
    import sys
    tasks_status: Dict[str, Dict[str, Any]] = load_progress_state()

    while True:
        event = await queue.get()
        task = event['task']
        tasks_status[task] = event

        sys.stdout.write('\033c')  # clear screen
        for tname, ev in tasks_status.items():
            color = COLORS.get(ev['status'], COLORS['in_progress'])
            bar_length = 20
            filled = int(ev['percent'] / 100 * bar_length)
            bar = '#' * filled + '-' * (bar_length - filled)
            eta_str = f"ETA: {int(ev['eta'])}s" if ev.get('eta') else ''
            status_line = f"{color}[{tname}] {ev['status']} {ev['percent']}% |{bar}| {eta_str}{COLORS['reset']}"
            if ev.get('file'):
                status_line += f" -> {ev['file']}"
            print(status_line)
        sys.stdout.flush()
        queue.task_done()


async def websocket_server(queue: asyncio.Queue, host: str = 'localhost', port: int = 8765,
                          auth_token: Optional[str] = None, compression: bool = True):
    """WebSocket server with optional authentication and compression."""
    if not websockets:
        logging.error("WebSockets package not installed.")
        return

    async def handler(websocket, _path):
        # Optional authentication
        if auth_token:
            provided = await websocket.recv()
            if provided != auth_token:
                await websocket.close(code=4001, reason="Unauthorized")
                return

        async for event in async_iter_queue(queue):
            data = json.dumps(event)
            await websocket.send(data if not compression else data.encode('utf-8'))

    async with websockets.serve(handler, host, port, compression=compression):
        await asyncio.Future()  # Run forever


async def async_iter_queue(queue: asyncio.Queue):
    while True:
        event = await queue.get()
        yield event
        queue.task_done()


class BaseExporter:
    def __init__(self, outdir: Path, outstem: str, overwrite_existing_generated: bool):
        self.outdir = outdir
        self.outstem = outstem
        self.overwrite_existing_generated = overwrite_existing_generated
        self.logger = logging.getLogger(self.__class__.__name__)

    async def export(self, *args, **kwargs) -> None:
        raise NotImplementedError


class AudioExporter(BaseExporter):
    async def export(self, progress_queue: Optional[asyncio.Queue] = None, **kwargs) -> None:
        outfile = Path(self.outdir) / (self.outstem + '.aac')
        start_time = time.time()

        for percent in range(0, 101, 20):
            await asyncio.sleep(0.3)
            if progress_queue:
                await progress_queue.put(make_progress_event("AudioExport", "in_progress", percent, file=str(outfile), start_time=start_time))

        if progress_queue:
            await progress_queue.put(make_progress_event("AudioExport", "completed", 100, file=str(outfile), start_time=start_time))
        self.logger.info(f"Audio exported to {outfile}")


class VideoExporter(BaseExporter):
    async def export(self, progress_queue: Optional[asyncio.Queue] = None, **kwargs) -> None:
        outfile = Path(self.outdir) / (self.outstem + '.mkv')
        start_time = time.time()

        for percent in range(0, 101, 10):
            await asyncio.sleep(0.4)
            if progress_queue:
                await progress_queue.put(make_progress_event("VideoExport", "in_progress", percent, file=str(outfile), start_time=start_time))

        if progress_queue:
            await progress_queue.put(make_progress_event("VideoExport", "completed", 100, file=str(outfile), start_time=start_time))
        self.logger.info(f"Video exported to {outfile}")


class SubtitleExporter(BaseExporter):
    async def export(self, progress_queue: Optional[asyncio.Queue] = None, **kwargs) -> None:
        outfile = Path(self.outdir) / (self.outstem + '.condensed.srt')
        start_time = time.time()

        for percent in [0, 50, 100]:
            await asyncio.sleep(0.2)
            if progress_queue:
                await progress_queue.put(make_progress_event("SubtitleExport", "in_progress", percent, file=str(outfile), start_time=start_time))

        if progress_queue:
            await progress_queue.put(make_progress_event("SubtitleExport", "completed", 100, file=str(outfile), start_time=start_time))
        self.logger.info(f"Subtitles exported to {outfile}")


# ------------------ Example CLI Usage ------------------

async def main():
    progress_queue = asyncio.Queue()

    # Start color-coded progress bar display
    asyncio.create_task(render_progress(progress_queue))

    # Optionally start WebSocket server for progress streaming
    if websockets:
        asyncio.create_task(websocket_server(progress_queue, auth_token="secret", compression=True))

    # Simulate running exports
    exporters = [
        AudioExporter(Path('out'), 'output', True),
        VideoExporter(Path('out'), 'output', True),
        SubtitleExporter(Path('out'), 'output', True)
    ]

    tasks = [exp.export(progress_queue=progress_queue) for exp in exporters]
    await asyncio.gather(*tasks)

# Usage: asyncio.run(main())
