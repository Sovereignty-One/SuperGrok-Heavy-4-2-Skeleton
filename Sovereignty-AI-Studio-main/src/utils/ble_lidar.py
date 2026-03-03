"""
BLE + LiDAR Module for Wireless EEG Connectivity
Provides Bluetooth Low Energy device management and
LiDAR spatial mapping for wireless EEG headset positioning.

Designed for enterprise-grade wireless EEG deployments
with real-time signal quality monitoring.
"""
import logging
import struct
from typing import Optional, Dict, Any, List
from enum import Enum
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class BLEDeviceType(str, Enum):
    """Supported BLE device types."""
    EEG_HEADSET = "eeg_headset"
    LIDAR_SENSOR = "lidar_sensor"
    HEART_RATE = "heart_rate"
    MOTION = "motion"


class ConnectionState(str, Enum):
    """BLE connection states."""
    DISCONNECTED = "disconnected"
    SCANNING = "scanning"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    STREAMING = "streaming"
    ERROR = "error"


@dataclass
class BLEDevice:
    """Represents a discovered or connected BLE device."""
    address: str
    name: str
    device_type: BLEDeviceType
    rssi: int = -100
    state: ConnectionState = ConnectionState.DISCONNECTED
    services: List[str] = field(default_factory=list)
    battery_level: Optional[int] = None
    signal_quality: float = 0.0


# Standard BLE UUIDs for EEG devices
EEG_SERVICE_UUID = "0000181a-0000-1000-8000-00805f9b34fb"
EEG_CHARACTERISTIC_UUID = "00002a6e-0000-1000-8000-00805f9b34fb"
BATTERY_SERVICE_UUID = "0000180f-0000-1000-8000-00805f9b34fb"


class BLEManager:
    """
    BLE device manager for wireless EEG headsets.
    Manages scanning, connection, and data streaming.
    """

    def __init__(self):
        self._devices: Dict[str, BLEDevice] = {}
        self._state = ConnectionState.DISCONNECTED
        self._active_device: Optional[str] = None

    def get_status(self) -> Dict[str, Any]:
        """Get BLE manager status."""
        return {
            "state": self._state.value,
            "active_device": self._active_device,
            "discovered_devices": len(self._devices),
            "devices": [
                {
                    "address": d.address,
                    "name": d.name,
                    "type": d.device_type.value,
                    "rssi": d.rssi,
                    "state": d.state.value,
                    "battery": d.battery_level,
                    "signal_quality": d.signal_quality,
                }
                for d in self._devices.values()
            ],
        }

    def start_scan(self, timeout: float = 10.0) -> Dict[str, Any]:
        """
        Start BLE device scanning.

        Args:
            timeout: Scan duration in seconds
        """
        self._state = ConnectionState.SCANNING
        logger.info(f"BLE scan started (timeout={timeout}s)")
        return {
            "status": "scanning",
            "timeout": timeout,
            "message": "Scanning for BLE EEG devices...",
        }

    def register_device(
        self,
        address: str,
        name: str,
        device_type: str = "eeg_headset",
        rssi: int = -60,
    ) -> Dict[str, Any]:
        """Register a discovered BLE device."""
        try:
            dev_type = BLEDeviceType(device_type)
        except ValueError:
            dev_type = BLEDeviceType.EEG_HEADSET

        device = BLEDevice(
            address=address,
            name=name,
            device_type=dev_type,
            rssi=rssi,
            state=ConnectionState.DISCONNECTED,
        )
        self._devices[address] = device
        logger.info(f"BLE device registered: {name} ({address})")
        return {
            "address": address,
            "name": name,
            "type": dev_type.value,
            "registered": True,
        }

    def connect(self, address: str) -> Dict[str, Any]:
        """Connect to a BLE device."""
        if address not in self._devices:
            return {"error": "Device not found", "connected": False}

        device = self._devices[address]
        device.state = ConnectionState.CONNECTED
        self._active_device = address
        self._state = ConnectionState.CONNECTED
        logger.info(f"BLE connected: {device.name} ({address})")
        return {
            "address": address,
            "name": device.name,
            "connected": True,
            "state": device.state.value,
        }

    def disconnect(self, address: Optional[str] = None) -> Dict[str, Any]:
        """Disconnect from a BLE device."""
        addr = address or self._active_device
        if addr and addr in self._devices:
            self._devices[addr].state = ConnectionState.DISCONNECTED
            if self._active_device == addr:
                self._active_device = None
                self._state = ConnectionState.DISCONNECTED
            return {"disconnected": True, "address": addr}
        return {"disconnected": False, "error": "No active device"}

    def get_signal_quality(self, address: Optional[str] = None) -> Dict[str, Any]:
        """Get signal quality metrics for connected device."""
        addr = address or self._active_device
        if not addr or addr not in self._devices:
            return {"error": "No device connected"}

        device = self._devices[addr]
        # Signal quality calculation from RSSI
        if device.rssi >= -50:
            quality = 1.0
        elif device.rssi >= -70:
            quality = 0.75
        elif device.rssi >= -85:
            quality = 0.5
        else:
            quality = 0.25

        device.signal_quality = quality
        return {
            "address": addr,
            "rssi": device.rssi,
            "signal_quality": quality,
            "quality_label": (
                "excellent" if quality >= 0.75
                else "good" if quality >= 0.5
                else "fair" if quality >= 0.25
                else "poor"
            ),
        }


class LiDARMapper:
    """
    LiDAR spatial mapper for EEG headset positioning.
    Provides 3D spatial awareness for device tracking.
    """

    def __init__(self):
        self._scan_data: List[Dict[str, float]] = []
        self._active = False

    def get_status(self) -> Dict[str, Any]:
        """Get LiDAR mapper status."""
        return {
            "active": self._active,
            "point_count": len(self._scan_data),
        }

    def start_mapping(self) -> Dict[str, Any]:
        """Start LiDAR spatial mapping."""
        self._active = True
        logger.info("LiDAR mapping started")
        return {"status": "mapping", "message": "LiDAR spatial mapping active"}

    def stop_mapping(self) -> Dict[str, Any]:
        """Stop LiDAR spatial mapping."""
        self._active = False
        return {
            "status": "stopped",
            "points_collected": len(self._scan_data),
        }

    def add_point(self, x: float, y: float, z: float) -> Dict[str, Any]:
        """Add a LiDAR scan point."""
        point = {"x": x, "y": y, "z": z}
        self._scan_data.append(point)
        return {"point": point, "total_points": len(self._scan_data)}

    def get_scan_data(self, limit: int = 100) -> List[Dict[str, float]]:
        """Get collected scan data points."""
        return self._scan_data[-limit:]


# Global instances
ble_manager = BLEManager()
lidar_mapper = LiDARMapper()
