"""Dataclasses modeling Teltonika Codec 8 / 8E AVL frames."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class GpsElement:
    """GPS telemetry positioning element inside an AVL record."""

    longitude: float
    latitude: float
    altitude_m: int
    angle: int
    satellites: int
    speed_kmh: int


@dataclass
class AvlRecord:
    """Single AVL telemetry record extracted from a Codec 8 / 8E packet."""

    timestamp: datetime
    priority: int
    gps: GpsElement
    event_io_id: int
    io_elements: dict[int, int] = field(default_factory=dict)
    io_nx_elements: dict[int, bytes] = field(default_factory=dict)


@dataclass
class AvlDataPacket:
    """Full parsed Teltonika TCP payload containing one or more AVL records."""

    codec_id: int
    record_count: int
    records: list[AvlRecord] = field(default_factory=list)
    crc_valid: bool = True

    @property
    def ack_frame(self) -> bytes:
        """4-byte big-endian acknowledgment expected by Teltonika devices."""
        return self.record_count.to_bytes(4, byteorder="big")
