"""Tests for Teltonika Codec 8 and Codec 8 Extended binary packet parsing."""

import struct
import unittest
from datetime import datetime, timezone

from teltonika_codec8.crc16 import crc16_ibm
from teltonika_codec8.parser import CODEC_8, CODEC_8_EXTENDED, TeltonikaCodecParser


def _build_codec8e_packet(
    lat: float,
    lon: float,
    speed: int,
    io_1b: dict[int, int],
    io_2b: dict[int, int],
    io_nx: dict[int, bytes] | None = None,
) -> bytes:
    """Construct a valid Teltonika Codec 8 Extended packet with CRC-16."""
    ts_ms = int(datetime(2026, 10, 15, 12, 0, 0, tzinfo=timezone.utc).timestamp() * 1000)
    lon_raw = int(lon * 10_000_000)
    lat_raw = int(lat * 10_000_000)

    body = bytearray()
    body.append(CODEC_8_EXTENDED)  # Codec ID 0x8E
    body.append(1)  # 1 record

    # Record header + GPS
    body.extend(struct.pack(">QB", ts_ms, 0))  # ts, priority
    body.extend(struct.pack(">iihHBH", lon_raw, lat_raw, 120, 90, 12, speed))

    io_nx = io_nx or {}
    total_io = len(io_1b) + len(io_2b) + len(io_nx)
    body.extend(struct.pack(">HH", 239, total_io))  # event_io_id=239, total_io

    # 1-byte IO
    body.extend(struct.pack(">H", len(io_1b)))
    for k, v in io_1b.items():
        body.extend(struct.pack(">HB", k, v))

    # 2-byte IO
    body.extend(struct.pack(">H", len(io_2b)))
    for k, v in io_2b.items():
        body.extend(struct.pack(">HH", k, v))

    # 4-byte IO, 8-byte IO
    body.extend(struct.pack(">HH", 0, 0))

    # NX variable-length IO
    body.extend(struct.pack(">H", len(io_nx)))
    for k, v in io_nx.items():
        body.extend(struct.pack(">HH", k, len(v)))
        body.extend(v)

    body.append(1)  # record count repeat

    crc = crc16_ibm(bytes(body))
    frame = struct.pack(">II", 0, len(body)) + bytes(body) + struct.pack(">I", crc)
    return frame


class TestTeltonikaParser(unittest.TestCase):
    def test_imei_handshake(self) -> None:
        imei = b"352093081234567"
        frame = struct.pack(">H", len(imei)) + imei
        parsed = TeltonikaCodecParser.parse_imei_handshake(frame)
        self.assertEqual(parsed, "352093081234567")

        # Invalid short IMEI
        bad = struct.pack(">H", 3) + b"123"
        self.assertIsNone(TeltonikaCodecParser.parse_imei_handshake(bad))

    def test_parse_codec8_extended_packet_with_crc_and_nx(self) -> None:
        frame = _build_codec8e_packet(
            lat=52.2297,
            lon=21.0122,
            speed=85,
            io_1b={239: 1},  # ignition=1
            io_2b={36: 2150},  # RPM=2150
            io_nx={281: b"P0205"},  # DTC variable-length IO
        )

        pkt = TeltonikaCodecParser.parse(frame)
        self.assertTrue(pkt.crc_valid)
        self.assertEqual(pkt.codec_id, CODEC_8_EXTENDED)
        self.assertEqual(pkt.record_count, 1)
        self.assertEqual(pkt.ack_frame, b"\x00\x00\x00\x01")

        rec = pkt.records[0]
        self.assertAlmostEqual(rec.gps.latitude, 52.2297, places=4)
        self.assertAlmostEqual(rec.gps.longitude, 21.0122, places=4)
        self.assertEqual(rec.gps.speed_kmh, 85)
        self.assertEqual(rec.io_elements[239], 1)
        self.assertEqual(rec.io_elements[36], 2150)
        self.assertEqual(rec.io_nx_elements[281], b"P0205")

    def test_corrupted_crc_detected(self) -> None:
        frame = bytearray(
            _build_codec8e_packet(lat=50.0, lon=19.0, speed=0, io_1b={239: 0}, io_2b={})
        )
        frame[-1] ^= 0xFF  # Corrupt last byte of CRC
        pkt = TeltonikaCodecParser.parse(bytes(frame))
        self.assertFalse(pkt.crc_valid)


if __name__ == "__main__":
    unittest.main()
