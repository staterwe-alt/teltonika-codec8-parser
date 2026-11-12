"""Tests for Teltonika CRC-16 IBM checksum verification."""

import unittest

from teltonika_codec8.crc16 import crc16_ibm, verify_crc16


class TestCRC16(unittest.TestCase):
    def test_crc16_empty(self) -> None:
        self.assertEqual(crc16_ibm(b""), 0x0000)

    def test_crc16_known_vector(self) -> None:
        # Standard IBM CRC vector: "123456789" -> 0xBB3D
        self.assertEqual(crc16_ibm(b"123456789"), 0xBB3D)
        self.assertTrue(verify_crc16(b"123456789", 0xBB3D))
        self.assertFalse(verify_crc16(b"123456789", 0x1234))


if __name__ == "__main__":
    unittest.main()
