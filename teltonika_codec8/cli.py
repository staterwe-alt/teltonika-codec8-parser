"""CLI tool for decoding Teltonika Codec 8 / 8E hex strings and DTC fault codes."""

from __future__ import annotations

import argparse
import json
import sys

from teltonika_codec8 import __version__
from teltonika_codec8.dtc import decode_dtc_int
from teltonika_codec8.parser import TeltonikaCodecParser


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="teltonika-parser",
        description="Decode Teltonika Codec 8 / 8 Extended AVL packets and SAE J2012 DTC codes.",
    )
    parser.add_argument("-v", "--version", action="version", version=f"teltonika-codec8 {__version__}")

    sub = parser.add_subparsers(dest="command", required=True)

    p_decode = sub.add_parser("decode", help="Decode a hex AVL packet.")
    p_decode.add_argument("hex_payload", help="Hexadecimal AVL packet string.")
    p_decode.add_argument("--no-crc", action="store_true", help="Skip CRC-16 validation.")

    p_dtc = sub.add_parser("dtc", help="Decode raw integer/hex SAE J2012 DTC code.")
    p_dtc.add_argument("code", help="Raw 16-bit DTC hex (e.g. 0x0205) or integer.")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "dtc":
        raw_val = int(args.code, 16) if args.code.lower().startswith("0x") else int(args.code)
        sys.stdout.write(decode_dtc_int(raw_val) + "\n")
        return 0

    if args.command == "decode":
        try:
            packet = TeltonikaCodecParser.parse_hex(
                args.hex_payload, verify_checksum=not args.no_crc
            )
        except Exception as exc:
            sys.stderr.write(f"Error decoding packet: {exc}\n")
            return 1

        output = {
            "codec_id": f"0x{packet.codec_id:02X}",
            "record_count": packet.record_count,
            "crc_valid": packet.crc_valid,
            "records": [
                {
                    "timestamp": rec.timestamp.isoformat(),
                    "priority": rec.priority,
                    "gps": {
                        "latitude": rec.gps.latitude,
                        "longitude": rec.gps.longitude,
                        "altitude_m": rec.gps.altitude_m,
                        "angle": rec.gps.angle,
                        "satellites": rec.gps.satellites,
                        "speed_kmh": rec.gps.speed_kmh,
                    },
                    "event_io_id": rec.event_io_id,
                    "io_elements": rec.io_elements,
                }
                for rec in packet.records
            ],
        }
        sys.stdout.write(json.dumps(output, indent=2) + "\n")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
