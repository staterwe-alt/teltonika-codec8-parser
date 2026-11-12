"""Tests for teltonika-parser CLI commands."""

import io
import json
import unittest
from contextlib import redirect_stdout

from tests.test_parser import _build_codec8e_packet
from teltonika_codec8.cli import main


class TestCLI(unittest.TestCase):
    def test_cli_dtc_decode(self) -> None:
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = main(["dtc", "0x0205"])
        self.assertEqual(rc, 0)
        self.assertEqual(buf.getvalue().strip(), "P0205")

    def test_cli_decode_hex_packet(self) -> None:
        frame = _build_codec8e_packet(
            lat=51.1079,
            lon=17.0385,
            speed=62,
            io_1b={239: 1},
            io_2b={36: 1800},
        )
        hex_str = frame.hex()
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = main(["decode", hex_str])
        self.assertEqual(rc, 0)
        data = json.loads(buf.getvalue())
        self.assertTrue(data["crc_valid"])
        self.assertEqual(data["records"][0]["gps"]["speed_kmh"], 62)
        self.assertEqual(data["records"][0]["io_elements"]["36"], 1800)


if __name__ == "__main__":
    unittest.main()
