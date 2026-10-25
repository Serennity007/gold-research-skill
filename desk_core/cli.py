"""CLI surface shared by standalone Skills and the sector workbench."""
import argparse
import csv
import json
import sys
from pathlib import Path
from .bundle import run, verify, replay


def main(expected_profile=None):
    parser = argparse.ArgumentParser(description="Offline futures research desk; Python 3.10+; no third-party dependencies")
    commands = parser.add_subparsers(dest="command", required=True)
    execute = commands.add_parser("run", help="validate inputs and create both English and Chinese reports")
    execute.add_argument("--config", type=Path, required=True)
    execute.add_argument("--out", type=Path, required=True)
    execute.add_argument("--lang", choices=("en", "zh-CN"), default="en")
    check = commands.add_parser("verify", help="check exact bundle file set and SHA-256")
    check.add_argument("directory", type=Path)
    rerun = commands.add_parser("replay", help="verify and reproduce frozen inputs with the same engine")
    rerun.add_argument("directory", type=Path)
    rerun.add_argument("--out", type=Path, required=True)
    rerun.add_argument("--lang", choices=("en", "zh-CN"), default="en")
    args = parser.parse_args()
    try:
        if args.command == "verify":
            manifest = verify(args.directory)
            result = {"status": "verified", "files": len(manifest["files"])}
        else:
            directory = run(args.config, args.out, args.lang, expected_profile) if args.command == "run" else replay(args.directory, args.out, args.lang, expected_profile)
            result = {"status": "complete", "directory": str(directory.resolve()), "report": str((directory/"index.html").resolve())}
    except (ValueError, OSError, KeyError, TypeError, OverflowError, csv.Error, RecursionError) as exc:
        print(json.dumps({"status": "error", "message": str(exc)}, ensure_ascii=True), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=True))
    return 0
