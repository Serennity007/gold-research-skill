"""Compatibility adapter: hashed new legacy reports, input-only old evidence.

Copied identically into the four standalone research scripts directories.
"""
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from desk_core.bundle import seal, verify
from desk_core.validation import inside, read_json, require


def verify_snapshot(config_path):
    config_path=Path(config_path)
    root=config_path.parent
    completion=read_json(inside(root,"COMPLETE.json").read_bytes())
    if completion.get("schema_version")==3:
        verify(root)
        return "hashed_artifacts"
    # Old committed demonstrations remain unchanged. Their recorded input hashes
    # can be checked; their reports were not covered by a completion hash.
    require(completion.get("status")=="complete","incomplete legacy snapshot")
    config=read_json(config_path.read_bytes())
    payload=read_json(inside(root,"bundle.json").read_bytes())
    require(set(config["files"])==set(payload["inputs"]),"legacy input role mismatch")
    for role,name in config["files"].items():
        require(hashlib.sha256(inside(root,name).read_bytes()).hexdigest()==payload["inputs"][role]["sha256"],"legacy input hash mismatch: "+role)
    return "legacy_input_hashes_only"


if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory",type=Path)
    args=parser.parse_args()
    try:
        assurance=verify_snapshot(args.directory/"config.snapshot.json")
    except (ValueError,OSError,KeyError,TypeError) as exc:
        parser.exit(2,"ERROR: "+str(exc)+"\n")
    print(json.dumps({"status":"verified","assurance":assurance}))
