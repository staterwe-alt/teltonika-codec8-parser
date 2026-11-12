# teltonika-codec8-parser

Lightweight, zero-dependency Python parser for Teltonika Codec 8 and Codec 8 Extended binary telemetry packets with CRC-16 IBM verification and SAE J2012 DTC fault code decoding.

## Features

- **Full Codec 8 & Codec 8 Extended Support:** Decodes both 0x08 and 0x8E protocol variants.
- **Hardware-Accurate Checksums:** Verifies 16-bit CRC-IBM checksums against incoming payloads.
- **DTC Diagnostic Decoder:** Translates raw 16-bit ECU trouble codes into standard SAE J2012 formats (P/C/B/U).
- **Zero External Dependencies:** Built solely on Python 3.11+ standard library.
- **CLI Utility:** Quickly inspect hex strings or decode DTC fault codes directly from the terminal.

## Quick Start

```bash
# Decode raw diagnostic trouble code
python -m teltonika_codec8 dtc 0x0205
# Returns: P0205

# Decode AVL telemetry frame from hex string
python -m teltonika_codec8 decode 00000000000...
```

## Running Tests

```bash
python -m unittest discover -s tests -v
```
