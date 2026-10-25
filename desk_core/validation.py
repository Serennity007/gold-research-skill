"""Strict local data contracts. Source declarations are not authentication."""
import csv
import hashlib
import io
import json
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path, PurePosixPath

MAX_BYTES = 16 * 1024 * 1024


def require(condition, message):
    if not condition:
        raise ValueError(message)


def stamp(value):
    require(isinstance(value, str) and bool(value.strip()), "timestamp must be a string")
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(result.tzinfo is not None and result.utcoffset() is not None,
            "timestamp requires an explicit UTC offset")
    return result.astimezone(timezone.utc)


def day(value):
    require(isinstance(value, str) and len(value) == 10, "expected YYYY-MM-DD")
    parsed = date.fromisoformat(value)
    require(parsed.isoformat() == value, "expected canonical YYYY-MM-DD")
    return parsed


def dec(value, minimum=None, positive=False):
    require(not isinstance(value, (bool, dict, list)) and value is not None, "invalid numeric value")
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError("invalid decimal value") from exc
    require(result.is_finite(), "nonfinite numeric value")
    require(not positive or result > 0, "value must be positive")
    require(minimum is None or result >= minimum, "value below minimum")
    require(abs(result) <= Decimal("1e24"), "numeric value exceeds supported range")
    return result


def integer(value, minimum=0):
    result = dec(value, minimum)
    require(result == result.to_integral_value(), "integer required")
    return int(result)


def object_pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON key: " + key)
        result[key] = value
    return result


def read_json(raw):
    require(len(raw) <= MAX_BYTES, "input exceeds 16 MiB")
    def invalid(value):
        raise ValueError("invalid JSON constant: " + value)
    return json.loads(raw.decode("utf-8-sig"), object_pairs_hook=object_pairs,
                      parse_constant=invalid)


def csv_rows(raw, required):
    require(len(raw) <= MAX_BYTES, "input exceeds 16 MiB")
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")), strict=True)
    headers = reader.fieldnames or []
    require(bool(headers) and len(headers) == len(set(headers)), "missing/duplicate CSV headers")
    require(set(required) <= set(headers), "missing CSV columns: " + ", ".join(sorted(set(required)-set(headers))))
    result = list(reader)
    require(bool(result), "empty CSV input")
    require(len(result) <= 100000, "input exceeds 100000 rows")
    require(all(None not in row and all(v is not None for v in row.values()) for row in result),
            "CSV row width does not match header")
    return result


def inside(root, value):
    require(isinstance(value, str) and value and "\\" not in value and ":" not in value,
            "input must be a portable relative path")
    part = PurePosixPath(value)
    require(not part.is_absolute() and ".." not in part.parts and value == part.as_posix(),
            "unsafe relative path")
    root = Path(root).resolve()
    target = root.joinpath(*part.parts)
    for parent in [target, *target.parents]:
        if parent == root:
            break
        require(not parent.is_symlink() and not (hasattr(parent, "is_junction") and parent.is_junction()),
                "linked inputs are not supported")
    resolved = target.resolve()
    require(resolved.is_relative_to(root) and resolved.is_file(), "input escapes root or is not a file")
    require(resolved.stat().st_size <= MAX_BYTES, "input exceeds 16 MiB")
    return resolved


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def dumps(value):
    def encode(item):
        if isinstance(item, Decimal):
            return format(item, "f")
        raise TypeError(type(item).__name__)
    return json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False, default=encode) + "\n"


def source(config, role, cutoff):
    if config["data_kind"] == "synthetic":
        return {"name": "Constructed example", "policy": "synthetic"}
    item = config.get("sources", {}).get(role)
    require(isinstance(item, dict) and bool(str(item.get("name", "")).strip()), "source name required: " + role)
    retrieved = stamp(item["retrieved_at"])
    require(item.get("policy") in ("retrieval_snapshot", "archived_publication"), "explicit source policy required")
    if item["policy"] == "archived_publication":
        require(bool(str(item.get("archive_reference", "")).strip()), "archive_reference required")
    else:
        require(retrieved <= cutoff, "retrieval after as_of cannot establish historical availability")
    return dict(item)


def visible(row, cutoff, provenance):
    observed, published, available = (stamp(row[k]) for k in ("observed_at", "published_at", "available_at"))
    require(observed <= published <= available, "require observed_at <= published_at <= available_at")
    if provenance["policy"] == "retrieval_snapshot":
        require(available >= stamp(provenance["retrieved_at"]), "retrieved snapshot cannot claim earlier availability")
    return available <= cutoff


def vintages(rows, identity, cutoff, provenance):
    """One as-of vintage per event; conflicting identical clocks are never guessed."""
    selected, seen, excluded = {}, set(), 0
    for row in rows:
        event = tuple(stamp(row[k]) if k in ("observed_at", "published_at", "available_at") else row[k] for k in identity)
        key = (*event, stamp(row["published_at"]), stamp(row["available_at"]))
        require(key not in seen, "duplicate/conflicting vintage")
        seen.add(key)
        if not visible(row, cutoff, provenance):
            excluded += 1
            continue
        previous = selected.get(event)
        if previous is None or (stamp(row["published_at"]), stamp(row["available_at"])) > (
                stamp(previous["published_at"]), stamp(previous["available_at"])):
            selected[event] = row
    return list(selected.values()), excluded
