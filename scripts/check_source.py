#!/usr/bin/env python3
"""Emit exact SHA256 used by ControlSub for UTF-8 source blobs.
Usage: python scripts/check_source.py path/to/source.yml
This does not publish the source and does not attest the repository owner.
"""
from pathlib import Path
import argparse
import hashlib

p=argparse.ArgumentParser()
p.add_argument('source', type=Path)
a=p.parse_args()
raw=a.source.read_bytes()
if not (20 <= len(raw) <= 6000):
    p.error('ControlSub requires 20..6000 bytes per source')
try: raw.decode('utf-8')
except UnicodeDecodeError: p.error('source must be UTF-8 text')
print(hashlib.sha256(raw).hexdigest())
