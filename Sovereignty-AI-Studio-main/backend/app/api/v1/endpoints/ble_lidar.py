"""
BLE and LiDAR API endpoints for wireless EEG connectivity.
Manages BLE device scanning, connection, and LiDAR spatial mapping.
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class BLEDeviceRegister(BaseModel):
    address: str
    name: str
    device_type: str = "eeg_headset"
    rssi: int = -60


class LiDARPoint(BaseModel):
    x: float
    y: float
    z: float


@router.get("/status", response_model=dict)
async def get_ble_status():
    """Get BLE manager and LiDAR mapper status."""
    from src.utils.ble_lidar import ble_manager, lidar_mapper
    return {
        "ble": ble_manager.get_status(),
        "lidar": lidar_mapper.get_status(),
    }


@router.post("/scan", response_model=dict)
async def start_ble_scan(timeout: float = Query(10.0, ge=1.0, le=60.0)):
    """Start scanning for BLE EEG devices."""
    from src.utils.ble_lidar import ble_manager
    return ble_manager.start_scan(timeout)


@router.post("/device", response_model=dict, status_code=201)
async def register_device(device: BLEDeviceRegister):
    """Register a discovered BLE device."""
    from src.utils.ble_lidar import ble_manager
    return ble_manager.register_device(
        address=device.address,
        name=device.name,
        device_type=device.device_type,
        rssi=device.rssi,
    )


@router.post("/connect/{address}", response_model=dict)
async def connect_device(address: str):
    """Connect to a registered BLE device."""
    from src.utils.ble_lidar import ble_manager
    result = ble_manager.connect(address)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/disconnect", response_model=dict)
async def disconnect_device(address: Optional[str] = None):
    """Disconnect from a BLE device."""
    from src.utils.ble_lidar import ble_manager
    return ble_manager.disconnect(address)


@router.get("/signal-quality", response_model=dict)
async def get_signal_quality(address: Optional[str] = None):
    """Get signal quality metrics for connected device."""
    from src.utils.ble_lidar import ble_manager
    result = ble_manager.get_signal_quality(address)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/lidar/start", response_model=dict)
async def start_lidar():
    """Start LiDAR spatial mapping."""
    from src.utils.ble_lidar import lidar_mapper
    return lidar_mapper.start_mapping()


@router.post("/lidar/stop", response_model=dict)
async def stop_lidar():
    """Stop LiDAR spatial mapping."""
    from src.utils.ble_lidar import lidar_mapper
    return lidar_mapper.stop_mapping()


@router.post("/lidar/point", response_model=dict)
async def add_lidar_point(point: LiDARPoint):
    """Add a LiDAR scan point."""
    from src.utils.ble_lidar import lidar_mapper
    return lidar_mapper.add_point(point.x, point.y, point.z)


@router.get("/lidar/points", response_model=list)
async def get_lidar_points(limit: int = Query(100, ge=1, le=1000)):
    """Get collected LiDAR scan data points."""
    from src.utils.ble_lidar import lidar_mapper
    return lidar_mapper.get_scan_data(limit)
