"""Small local-input helpers; this module performs no network or trading operations."""
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
import math
from pathlib import Path


def timestamp(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timestamps require an explicit timezone")
    return parsed.astimezone(timezone.utc)


def number(value, positive=False):
    result = float(value)
    if not math.isfinite(result) or (positive and result <= 0):
        raise ValueError("invalid finite price/value")
    return result


def records(raw, required):
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
    if not set(required).issubset(reader.fieldnames or []):
        raise ValueError("missing columns: " + ",".join(required))
    result = list(reader)
    if not result:
        raise ValueError("input contains no observations")
    return result


def provenance(raw):
    return hashlib.sha256(raw).hexdigest()


def emit(result, output, inputs):
    output = Path(output)
    if output.resolve() in {Path(p).resolve() for p in inputs}:
        raise ValueError("output must not overwrite input")
    result["generated_at_utc"] = datetime.now(timezone.utc).isoformat()
    body = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(body)


def kind(value):
    if value not in ("synthetic", "imported_observations"):
        raise ValueError("explicit data kind required")
    return value
