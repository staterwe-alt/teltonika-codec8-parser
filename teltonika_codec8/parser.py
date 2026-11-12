"""Binary decoder for Teltonika Codec 8 and Codec 8 Extended AVL packets."""

from __future__ import annotations

import struct
from datetime import datetime, timezone
from io import BytesIO

from teltonika_codec8.crc16 import verify_crc16
from teltonika_codec8.models import AvlDataPacket, AvlRecord, GpsElement

CODEC_8 = 0x08
CODEC_8_EXTENDED = 0x8E


class TeltonikaCodecParser:
    """Parses binary and hex AVL packets sent by Teltonika FMC/FMB trackers."""

    @staticmethod
    def parse_imei_handshake(data: bytes) -> str | None:
        """Parse IMEI from device initial registration handshake.

        Format: 2 bytes length (big-endian) + ASCII IMEI string.
        """
        if len(data) < 3:
            return None
        length = int.from_bytes(data[:2], byteorder="big")
        if len(data) < 2 + length:
            return None
        try:
            imei_str = data[2 : 2 + length].decode("ascii").strip()
            if imei_str.isdigit() and len(imei_str) == 15:
                return imei_str
        except Exception:
            return None
        return None

    @classmethod
    def parse_hex(cls, hex_str: str, verify_checksum: bool = True) -> AvlDataPacket:
        """Parse packet from a hexadecimal string."""
        clean_hex = "".join(hex_str.split())
        return cls.parse(bytes.fromhex(clean_hex), verify_checksum=verify_checksum)

    @classmethod
    def parse(cls, data: bytes, verify_checksum: bool = True) -> AvlDataPacket:
        """Parse complete binary AVL data packet."""
        if len(data) < 12:
            raise ValueError(f"Packet too short ({len(data)} bytes, min 12)")

        # Read preamble (4 zero bytes) and data length (4 bytes)
        preamble, data_len = struct.unpack_from(">II", data, 0)
        offset = 8

        # If packet contains standard preamble
        if preamble == 0:
            content_bytes = data[offset : offset + data_len]
            crc_offset = offset + data_len
            expected_crc = None
            if len(data) >= crc_offset + 4:
                expected_crc = struct.unpack_from(">I", data, crc_offset)[0] & 0xFFFF
        else:
            # Fallback if raw content passed without 8-byte TCP header
            content_bytes = data
            expected_crc = None

        crc_valid = True
        if verify_checksum and expected_crc is not None:
            crc_valid = verify_crc16(content_bytes, expected_crc)

        stream = BytesIO(content_bytes)
        codec_id = struct.unpack(">B", stream.read(1))[0]

        if codec_id not in (CODEC_8, CODEC_8_EXTENDED):
            raise ValueError(f"Unsupported Codec ID: 0x{codec_id:02X} (expected 0x08 or 0x8E)")

        record_count = struct.unpack(">B", stream.read(1))[0]
        records: list[AvlRecord] = []

        is_extended = codec_id == CODEC_8_EXTENDED
        id_size = 2 if is_extended else 1
        cnt_size = 2 if is_extended else 1

        for _ in range(record_count):
            rec = cls._read_record(stream, id_size=id_size, cnt_size=cnt_size, is_extended=is_extended)
            records.append(rec)

        return AvlDataPacket(
            codec_id=codec_id,
            record_count=record_count,
            records=records,
            crc_valid=crc_valid,
        )

    @staticmethod
    def _read_int(stream: BytesIO, size: int, signed: bool = False) -> int:
        data = stream.read(size)
        if len(data) < size:
            raise ValueError(f"Unexpected EOF reading {size} bytes")
        return int.from_bytes(data, byteorder="big", signed=signed)

    @classmethod
    def _read_record(
        cls,
        stream: BytesIO,
        id_size: int,
        cnt_size: int,
        is_extended: bool,
    ) -> AvlRecord:
        # Timestamp (8 bytes UTC ms)
        ts_ms = cls._read_int(stream, 8)
        ts = datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc)

        priority = cls._read_int(stream, 1)

        # GPS Element (15 bytes)
        lon_raw = cls._read_int(stream, 4, signed=True)
        lat_raw = cls._read_int(stream, 4, signed=True)
        altitude = cls._read_int(stream, 2, signed=True)
        angle = cls._read_int(stream, 2)
        satellites = cls._read_int(stream, 1)
        speed = cls._read_int(stream, 2)

        gps = GpsElement(
            longitude=lon_raw / 10000000.0,
            latitude=lat_raw / 10000000.0,
            altitude_m=altitude,
            angle=angle,
            satellites=satellites,
            speed_kmh=speed,
        )

        event_io_id = cls._read_int(stream, id_size)
        total_io_count = cls._read_int(stream, cnt_size)

        io_elements: dict[int, int] = {}
        io_nx: dict[int, bytes] = {}

        # 1-byte IO
        cnt_1 = cls._read_int(stream, cnt_size)
        for _ in range(cnt_1):
            prop_id = cls._read_int(stream, id_size)
            io_elements[prop_id] = cls._read_int(stream, 1)

        # 2-byte IO
        cnt_2 = cls._read_int(stream, cnt_size)
        for _ in range(cnt_2):
            prop_id = cls._read_int(stream, id_size)
            io_elements[prop_id] = cls._read_int(stream, 2)

        # 4-byte IO
        cnt_4 = cls._read_int(stream, cnt_size)
        for _ in range(cnt_4):
            prop_id = cls._read_int(stream, id_size)
            io_elements[prop_id] = cls._read_int(stream, 4)

        # 8-byte IO
        cnt_8 = cls._read_int(stream, cnt_size)
        for _ in range(cnt_8):
            prop_id = cls._read_int(stream, id_size)
            io_elements[prop_id] = cls._read_int(stream, 8)

        # X-byte variable length IO (Codec 8 Extended only)
        if is_extended:
            cnt_x = cls._read_int(stream, 2)
            for _ in range(cnt_x):
                prop_id = cls._read_int(stream, 2)
                length = cls._read_int(stream, 2)
                val_bytes = stream.read(length)
                io_nx[prop_id] = val_bytes

        return AvlRecord(
            timestamp=ts,
            priority=priority,
            gps=gps,
            event_io_id=event_io_id,
            io_elements=io_elements,
            io_nx_elements=io_nx,
        )
