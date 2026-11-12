"""Tests for SAE J2012 OBD-II Diagnostic Trouble Code (DTC) decoding."""

import unittest

from teltonika_codec8.dtc import decode_dtc_bytes, decode_dtc_int


class TestDTC(unittest.TestCase):
    def test_decode_dtc_int_powertrain(self) -> None:
        # 0x0205 -> P0205 (Injector Circuit Malfunction - Cylinder 5)
        self.assertEqual(decode_dtc_int(0x0205), "P0205")
        # 0x0420 -> P0420 (Catalyst System Efficiency Below Threshold)
        self.assertEqual(decode_dtc_int(0x0420), "P0420")

    def test_decode_dtc_int_prefixes(self) -> None:
        # Chassis (0x4...), Body (0x8...), Network (0xC...)
        self.assertTrue(decode_dtc_int(0x4001).startswith("C"))
        self.assertTrue(decode_dtc_int(0x8001).startswith("B"))
        self.assertTrue(decode_dtc_int(0xC001).startswith("U"))

    def test_decode_dtc_bytes_ascii(self) -> None:
        raw = b"P0205,P0300"
        codes = decode_dtc_bytes(raw)
        self.assertEqual(codes, ["P0205", "P0300"])

    def test_decode_dtc_bytes_binary(self) -> None:
        raw = (0x0205).to_bytes(2, "big") + (0x0420).to_bytes(2, "big")
        codes = decode_dtc_bytes(raw)
        self.assertEqual(codes, ["P0205", "P0420"])


if __name__ == "__main__":
    unittest.main()
