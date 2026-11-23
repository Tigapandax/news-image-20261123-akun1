#!/usr/bin/env python3
"""Entrypoint for the news-image-20261123 make.fun entry.

The artwork is entry.png next to this file: a single-page newspaper
front page for Monday 23 November 2026, drawn at build time by draw.py.
It leads with the US-Iran naval confrontation near Hormuz, then covers
the Ukrainian sea-drone strike on the corvette Merkury off Benghazi,
the COP31 fallout in Antalya, the KOSPI sell-off, the Cikande factory
fire, Lahore's hazardous smog, and the rest of the day's news.

This program does two things, both with the standard library only:

1. Gate-check the artwork before anything is published: the file must
   be a well-formed PNG, exactly 1024 by 1024 pixels, no larger than
   1 MiB, and every chunk's CRC must verify. A corrupt or wrong-sized
   image fails loudly instead of being shipped.
2. Publish the validated bytes to the output directory
   (MAKEFUN_OUTPUT_DIR, default /output) as entry.png, then re-read
   what was written and confirm its SHA-256 matches the source.

Nothing here depends on the clock, randomness, or the network, so two
runs always produce byte-identical output.

Run locally with:  mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
"""

import hashlib
import os
import struct
import sys
import zlib
from pathlib import Path

# PNG file signature: 8 fixed bytes every PNG starts with.
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

# The competition's image gate.
EXPECTED_WIDTH = 1024
EXPECTED_HEIGHT = 1024
MAX_BYTES = 1024 * 1024  # 1 MiB

# Colour types the gate accepts: 2 = truecolour RGB, 6 = RGBA.
ACCEPTED_COLOUR_TYPES = (2, 6)

SOURCE_NAME = "entry.png"


class GateError(Exception):
    """Raised when the artwork fails any gate check."""


def _fail(message):
    raise GateError(message)


def read_chunks(data):
    """Yield (chunk_type, chunk_data) for each chunk in a PNG byte string.

    Walks the chunk stream by hand: a 4-byte big-endian length, a
    4-byte type, the payload, then a 4-byte CRC over type + payload.
    Any truncation, bad CRC, or missing IEND is an error, not a warning.
    """
    if data[: len(PNG_SIGNATURE)] != PNG_SIGNATURE:
        _fail("not a PNG file: bad 8-byte signature")

    offset = len(PNG_SIGNATURE)
    saw_iend = False
    while offset < len(data):
        header = data[offset : offset + 8]
        if len(header) < 8:
            _fail("truncated chunk header at byte %d" % offset)
        length, raw_type = struct.unpack(">I4s", header)
        chunk_type = raw_type.decode("latin-1")
        payload_start = offset + 8
        payload_end = payload_start + length
        crc_end = payload_end + 4
        if crc_end > len(data):
            _fail("chunk %s overruns the end of the file" % chunk_type)
        payload = data[payload_start:payload_end]
        stored_crc, = struct.unpack(">I", data[payload_end:crc_end])
        actual_crc = zlib.crc32(raw_type)
        actual_crc = zlib.crc32(payload, actual_crc)
        if actual_crc != stored_crc:
            _fail(
                "chunk %s has a bad CRC: stored %08x, computed %08x"
                % (chunk_type, stored_crc, actual_crc)
            )
        yield chunk_type, payload
        offset = crc_end
        if chunk_type == "IEND":
            saw_iend = True
            break
    if not saw_iend:
        _fail("PNG has no IEND chunk")
    if offset != len(data):
        _fail("trailing bytes after the IEND chunk")


def gate_image(data):
    """Run every gate check on the artwork bytes; return (width, height).

    Checks, in order: the file is not empty and fits the 1 MiB cap, the
    chunk stream is intact with valid CRCs, the first chunk is IHDR,
    and IHDR declares 1024x1024, 8-bit samples, an accepted colour
    type, and no interlacing.
    """
    if not data:
        _fail("entry.png is empty")
    if len(data) > MAX_BYTES:
        _fail(
            "entry.png is %d bytes, over the %d-byte limit"
            % (len(data), MAX_BYTES)
        )

    width = height = None
    first_chunk = True
    for chunk_type, payload in read_chunks(data):
        if first_chunk:
            if chunk_type != "IHDR":
                _fail("first chunk is %s, expected IHDR" % chunk_type)
            first_chunk = False
            if len(payload) != 13:
                _fail("IHDR is %d bytes, expected 13" % len(payload))
            (width, height, bit_depth, colour_type,
             compression, filter_method,
             interlace) = struct.unpack(">IIBBBBB", payload)
            if (width, height) != (EXPECTED_WIDTH, EXPECTED_HEIGHT):
                _fail(
                    "image is %dx%d, expected %dx%d"
                    % (width, height, EXPECTED_WIDTH, EXPECTED_HEIGHT)
                )
            if bit_depth != 8:
                _fail("bit depth is %d, expected 8" % bit_depth)
            if colour_type not in ACCEPTED_COLOUR_TYPES:
                _fail("colour type %d is not RGB or RGBA" % colour_type)
            if compression != 0 or filter_method != 0:
                _fail("unsupported compression or filter method in IHDR")
            if interlace != 0:
                _fail("interlaced PNGs are not accepted")
    if width is None:
        _fail("no IHDR chunk found")
    return width, height


def publish(source_bytes, out_dir):
    """Write the validated bytes and prove the copy is exact.

    Writes to a temporary name first, then renames into place, so a
    failed run never leaves a half-written entry.png behind. The
    finished file is hashed and compared with the source hash.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / SOURCE_NAME
    staging = out_dir / (SOURCE_NAME + ".tmp")
    expected_hash = hashlib.sha256(source_bytes).hexdigest()
    staging.write_bytes(source_bytes)
    staging.replace(target)
    written = target.read_bytes()
    written_hash = hashlib.sha256(written).hexdigest()
    if written_hash != expected_hash:
        _fail("written file hash %s != source hash %s"
              % (written_hash, expected_hash))
    return target, written_hash


def main():
    here = Path(__file__).resolve().parent
    source_path = here / SOURCE_NAME
    try:
        data = source_path.read_bytes()
    except OSError as exc:
        print("cannot read %s: %s" % (source_path, exc), file=sys.stderr)
        return 1

    try:
        width, height = gate_image(data)
    except GateError as exc:
        print("gate check failed: %s" % exc, file=sys.stderr)
        return 1

    out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    try:
        target, digest = publish(data, out_dir)
    except (GateError, OSError) as exc:
        print("publish failed: %s" % exc, file=sys.stderr)
        return 1

    print(
        "wrote %s (%dx%d, %d bytes, sha256 %s)"
        % (target, width, height, len(data), digest)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
