"""CRC-16 IBM checksum calculator for Teltonika AVL packets."""

from __future__ import annotations


def crc16_ibm(data: bytes) -> int:
    """Compute 16-bit CRC-IBM checksum matching Teltonika hardware specification."""
    crc = 0x0000
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc & 0xFFFF


def verify_crc16(packet_data: bytes, expected_crc: int) -> bool:
    """Verify that calculated CRC matches expected checksum."""
    return crc16_ibm(packet_data) == expected_crc
