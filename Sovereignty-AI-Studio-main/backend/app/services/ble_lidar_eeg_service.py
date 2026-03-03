"""
BLE LiDAR Wireless EEG Service – Bluetooth Low Energy integration for
wireless EEG headset connectivity and spatial awareness via LiDAR.

Manages BLE device discovery, connection state, EEG data streaming,
and LiDAR spatial mapping for the Sovereignty AI Studio.
"""
import uuid
import logging
from enum import Enum
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class DeviceType(str, Enum):
    EEG_HEADSET = "eeg_headset"
    LIDAR_SENSOR = "lidar_sensor"
    HYBRID = "hybrid"


class ConnectionState(str, Enum):
    DISCONNECTED = "disconnected"
    SCANNING = "scanning"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    STREAMING = "streaming"
    ERROR = "error"


class EEGBand(str, Enum):
    DELTA = "delta"
    THETA = "theta"
    ALPHA = "alpha"
    BETA = "beta"
    GAMMA = "gamma"


@dataclass
class BLEDevice:
    """Represents a discovered or connected BLE device."""
    device_id: str
    name: str
    device_type: DeviceType
    mac_address: str = ""
    state: ConnectionState = ConnectionState.DISCONNECTED
    rssi: int = -100
    battery_level: int = 100
    firmware_version: str = "1.0.0"
    channels: int = 8
    sample_rate: int = 256
    last_seen: str = ""

    def __post_init__(self):
        if not self.last_seen:
            self.last_seen = datetime.now(timezone.utc).isoformat()


@dataclass
class EEGReading:
    """Single EEG data point with band power values."""
    timestamp: str
    device_id: str
    channel_count: int
    band_powers: Dict[str, float] = field(default_factory=dict)
    raw_quality: float = 1.0
    label: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()
        if not self.band_powers:
            self.band_powers = {
                EEGBand.DELTA.value: 0.0,
                EEGBand.THETA.value: 0.0,
                EEGBand.ALPHA.value: 0.0,
                EEGBand.BETA.value: 0.0,
                EEGBand.GAMMA.value: 0.0,
            }


@dataclass
class LiDARFrame:
    """Single LiDAR spatial frame."""
    timestamp: str
    device_id: str
    point_count: int = 0
    range_min_m: float = 0.0
    range_max_m: float = 10.0
    fov_degrees: float = 360.0

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


class BLELidarEEGService:
    """Manages BLE device connections for wireless EEG and LiDAR."""

    def __init__(self):
        self._devices: Dict[str, BLEDevice] = {}
        self._eeg_buffer: List[EEGReading] = []
        self._lidar_buffer: List[LiDARFrame] = []
        logger.info("BLELidarEEGService initialised")

    # ── Device management ────────────────────────────────────────────

    def scan_devices(self) -> List[Dict[str, Any]]:
        """Simulate BLE device scan and return discovered devices."""
        discovered = [
            BLEDevice(
                device_id=str(uuid.uuid4()),
                name="Muse 2 EEG",
                device_type=DeviceType.EEG_HEADSET,
                mac_address="AA:BB:CC:DD:EE:01",
                rssi=-45,
                channels=4,
                sample_rate=256,
            ),
            BLEDevice(
                device_id=str(uuid.uuid4()),
                name="OpenBCI Cyton",
                device_type=DeviceType.EEG_HEADSET,
                mac_address="AA:BB:CC:DD:EE:02",
                rssi=-60,
                channels=8,
                sample_rate=250,
            ),
            BLEDevice(
                device_id=str(uuid.uuid4()),
                name="LiDAR Spatial Sensor",
                device_type=DeviceType.LIDAR_SENSOR,
                mac_address="AA:BB:CC:DD:EE:03",
                rssi=-55,
            ),
        ]
        for dev in discovered:
            self._devices[dev.device_id] = dev
        return [self._device_to_dict(d) for d in discovered]

    def connect_device(self, device_id: str) -> Dict[str, Any]:
        """Connect to a BLE device."""
        device = self._devices.get(device_id)
        if not device:
            return {"error": "Device not found", "device_id": device_id}

        device.state = ConnectionState.CONNECTING
        # Simulate connection
        device.state = ConnectionState.CONNECTED
        device.last_seen = datetime.now(timezone.utc).isoformat()

        logger.info("Connected to BLE device %s (%s)", device.name, device_id)
        return self._device_to_dict(device)

    def disconnect_device(self, device_id: str) -> Dict[str, Any]:
        device = self._devices.get(device_id)
        if not device:
            return {"error": "Device not found"}
        device.state = ConnectionState.DISCONNECTED
        return self._device_to_dict(device)

    def list_devices(self) -> List[Dict[str, Any]]:
        return [self._device_to_dict(d) for d in self._devices.values()]

    # ── EEG streaming ────────────────────────────────────────────────

    def start_eeg_stream(self, device_id: str) -> Dict[str, Any]:
        """Start EEG data streaming from a connected device."""
        device = self._devices.get(device_id)
        if not device:
            return {"error": "Device not found"}
        if device.device_type not in (DeviceType.EEG_HEADSET, DeviceType.HYBRID):
            return {"error": "Device does not support EEG"}
        if device.state != ConnectionState.CONNECTED:
            return {"error": "Device not connected"}

        device.state = ConnectionState.STREAMING
        logger.info("EEG streaming started on %s", device.name)
        return {
            "device_id": device_id,
            "state": device.state.value,
            "channels": device.channels,
            "sample_rate": device.sample_rate,
        }

    def get_eeg_reading(self, device_id: str) -> Dict[str, Any]:
        """Get latest EEG reading from device."""
        device = self._devices.get(device_id)
        if not device or device.state != ConnectionState.STREAMING:
            return {"error": "Device not streaming"}

        reading = EEGReading(
            timestamp=datetime.now(timezone.utc).isoformat(),
            device_id=device_id,
            channel_count=device.channels,
            band_powers={
                EEGBand.DELTA.value: 25.0,
                EEGBand.THETA.value: 18.0,
                EEGBand.ALPHA.value: 30.0,
                EEGBand.BETA.value: 20.0,
                EEGBand.GAMMA.value: 7.0,
            },
            raw_quality=0.95,
            label="calm",
        )
        self._eeg_buffer.append(reading)
        return {
            "timestamp": reading.timestamp,
            "device_id": reading.device_id,
            "channel_count": reading.channel_count,
            "band_powers": reading.band_powers,
            "raw_quality": reading.raw_quality,
            "label": reading.label,
        }

    # ── LiDAR ────────────────────────────────────────────────────────

    def get_lidar_frame(self, device_id: str) -> Dict[str, Any]:
        """Get latest LiDAR spatial frame."""
        device = self._devices.get(device_id)
        if not device or device.device_type not in (DeviceType.LIDAR_SENSOR, DeviceType.HYBRID):
            return {"error": "Not a LiDAR device"}

        frame = LiDARFrame(
            timestamp=datetime.now(timezone.utc).isoformat(),
            device_id=device_id,
            point_count=1024,
            range_min_m=0.1,
            range_max_m=8.5,
        )
        self._lidar_buffer.append(frame)
        return {
            "timestamp": frame.timestamp,
            "device_id": frame.device_id,
            "point_count": frame.point_count,
            "range_min_m": frame.range_min_m,
            "range_max_m": frame.range_max_m,
            "fov_degrees": frame.fov_degrees,
        }

    # ── Status ───────────────────────────────────────────────────────

    def get_status(self) -> Dict[str, Any]:
        connected = sum(
            1 for d in self._devices.values()
            if d.state in (ConnectionState.CONNECTED, ConnectionState.STREAMING)
        )
        return {
            "service": "ble_lidar_eeg",
            "status": "online",
            "discovered_devices": len(self._devices),
            "connected_devices": connected,
            "eeg_readings_buffered": len(self._eeg_buffer),
            "lidar_frames_buffered": len(self._lidar_buffer),
        }

    @staticmethod
    def _device_to_dict(device: BLEDevice) -> Dict[str, Any]:
        return {
            "device_id": device.device_id,
            "name": device.name,
            "device_type": device.device_type.value,
            "mac_address": device.mac_address,
            "state": device.state.value,
            "rssi": device.rssi,
            "battery_level": device.battery_level,
            "channels": device.channels,
            "sample_rate": device.sample_rate,
            "last_seen": device.last_seen,
        }


# Module-level singleton
ble_lidar_eeg_service = BLELidarEEGService()
