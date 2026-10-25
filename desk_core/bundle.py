"""Exact local bundle consistency, not digital signatures or source authentication."""
from datetime import datetime, timezone
from pathlib import Path
import uuid
from .validation import require, read_json, sha, dumps, inside
from .engine import analyze, CLOCKS
from .validation import csv_rows, vintages, stamp
from .reports import report


def code_hashes():
    root = Path(__file__).parent
    return {p.name: sha(p.read_bytes()) for p in sorted(root.iterdir()) if p.suffix in (".py", ".json")}


def seal(root, marker="COMPLETE.json"):
    root = Path(root)
    files = {p.relative_to(root).as_posix(): sha(p.read_bytes()) for p in sorted(root.rglob("*")) if p.is_file() and p.name != marker}
    (root/marker).write_text(dumps({"schema_version": 3, "status": "complete", "files": files}), encoding="utf-8", newline="\n")


def verify(root, marker="COMPLETE.json"):
    root = Path(root).resolve()
    manifest = read_json(inside(root, marker).read_bytes())
    require(type(manifest.get("schema_version")) is int and manifest["schema_version"] == 3 and manifest.get("status") == "complete", "hashed v3 completion manifest required")
    require(isinstance(manifest.get("files"), dict) and bool(manifest["files"]), "empty hash manifest")
    actual = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file() and p.relative_to(root).as_posix() != marker}
    require(actual == set(manifest["files"]), "bundle file set differs from manifest")
    for name, expected in manifest["files"].items():
        require(sha(inside(root, name).read_bytes()) == expected, "bundle hash mismatch: " + name)
    return manifest


def load(path, expected_profile=None):
    path = Path(path).resolve()
    if path.name == "config.snapshot.json":
        verify(path.parent)
    config_raw = path.read_bytes()
    config = read_json(config_raw)
    require(isinstance(config, dict) and isinstance(config.get("files"), dict), "configuration object/files required")
    if expected_profile is not None:
        require(config.get("profile") == expected_profile, "this Skill only accepts profile: " + expected_profile)
    raw = {role: inside(path.parent, value).read_bytes() for role,value in config["files"].items()}
    profiles = read_json((Path(__file__).parent/"profiles.json").read_bytes())
    result = analyze(config, raw, profiles)
    result["inputs"] = {role: {"sha256": sha(content), "bytes": len(content)} for role,content in raw.items()}
    result["config_sha256"] = sha(config_raw)
    result["engine_sha256"] = code_hashes()
    return config, raw, result


def run(config_path, output, lang="en", expected_profile=None):
    require(lang in ("en", "zh-CN"), "unsupported report language")
    config, raw, result = load(config_path, expected_profile)
    result["generated_at_utc"] = datetime.now(timezone.utc).isoformat()
    # Use the same vintage filter for the chart as for the calculation.
    rows = csv_rows(raw["bars"], CLOCKS + ["contract", "close"])
    bars, _ = vintages(rows, ["contract", "observed_at"], stamp(config["as_of"]), result["sources"]["bars"])
    bars.sort(key=lambda x: stamp(x["observed_at"]))
    reports = {language: report(result, bars, language) for language in ("en", "zh-CN")}
    directory = Path(output)/("desk-"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")+"-"+uuid.uuid4().hex[:8])
    directory.mkdir(parents=True, exist_ok=False)
    (directory/"inputs").mkdir()
    for role, content in raw.items():
        (directory/"inputs"/(role + (".json" if role == "spec" else ".csv"))).write_bytes(content)
    snapshot = dict(config, files={role: "inputs/"+role+(".json" if role=="spec" else ".csv") for role in raw})
    (directory/"config.snapshot.json").write_text(dumps(snapshot), encoding="utf-8", newline="\n")
    (directory/"bundle.json").write_text(dumps(result), encoding="utf-8", newline="\n")
    for language, (md, html) in reports.items():
        (directory/f"REPORT.{language}.md").write_text(md, encoding="utf-8", newline="\n")
        (directory/f"REPORT.{language}.html").write_text(html, encoding="utf-8", newline="\n")
    (directory/"REPORT.md").write_text(reports[lang][0], encoding="utf-8", newline="\n")
    (directory/"index.html").write_text(reports[lang][1], encoding="utf-8", newline="\n")
    seal(directory)
    verify(directory)
    return directory


def replay(root, output, lang="en", expected_profile=None):
    root = Path(root)
    verify(root)
    recorded = read_json((root/"bundle.json").read_bytes())
    require(recorded["engine_sha256"] == code_hashes(), "engine changed; use the recorded release for reproducible replay")
    directory = run(root/"config.snapshot.json", output, lang, expected_profile)
    actual = read_json((directory/"bundle.json").read_bytes())
    ignored = {"generated_at_utc", "config_sha256"}
    require({k:v for k,v in recorded.items() if k not in ignored} == {k:v for k,v in actual.items() if k not in ignored}, "replay calculations differ")
    return directory
