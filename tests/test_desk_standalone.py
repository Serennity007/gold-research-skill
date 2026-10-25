"""Portable regression tests copied to each independently installable specialist."""
import csv
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from desk_core.bundle import load, run, replay, verify, code_hashes
from desk_core.validation import csv_rows, read_json, dec
from desk_core.engine import analyze


class StandaloneDeskTests(unittest.TestCase):
    def setUp(self):
        config = next((ROOT/"examples/desk-demo").glob("*/config.json"))
        self.path=config
        self.config,self.raw,self.result=load(config)
        self.profiles=read_json((ROOT/"desk_core/profiles.json").read_bytes())

    def test_golden_core_values(self):
        self.assertEqual(self.result["market"]["atr14_simple"],4)
        self.assertEqual(self.result["basis"]["spot_minus_future"],5)
        self.assertEqual(self.result["fundamentals"][0]["prior_only_percentile"],50)
        self.assertEqual(self.result["quality"]["excluded_future_vintages"]["fundamentals"],1)

    def test_core_manifest_matches(self):
        manifest=read_json((ROOT/"CORE-MANIFEST.json").read_bytes())
        self.assertEqual(manifest["sha256"],code_hashes())

    def test_bundle_bilingual_replay_and_tamper(self):
        with tempfile.TemporaryDirectory() as temp:
            root=run(self.path,temp)
            for lang in ("en","zh-CN"):
                self.assertTrue((root/f"REPORT.{lang}.html").is_file())
            verify(root)
            replay(root,temp)
            (root/"inputs/bars.csv").write_text("tampered")
            with self.assertRaises(ValueError):
                replay(root,temp)

    def test_wrong_contract_rejected(self):
        rows=csv_rows(self.raw["bars"],[])
        rows[0]["contract"]="WRONG_ROLL"
        stream=io.StringIO(newline="")
        writer=csv.DictWriter(stream,fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
        self.raw["bars"]=stream.getvalue().encode("utf-8")
        with self.assertRaises(ValueError):
            analyze(self.config,self.raw,self.profiles)

    def test_invalid_number_and_csv_rejected(self):
        for value in (True,"NaN","Infinity"):
            with self.assertRaises(ValueError):
                dec(value)
        with self.assertRaises(ValueError):
            csv_rows(b"a,a\n1,2",[])

    def test_friday_night_calendar(self):
        self.config["as_of"]="2025-09-26T23:30:00+08:00"
        result=analyze(self.config,self.raw,self.profiles)
        self.assertEqual(result["market"]["calendar"]["latest_completed_trade_date"],"2025-09-26")
        self.config["as_of"]="2025-09-29T15:10:00+08:00"
        self.assertEqual(analyze(self.config,self.raw,self.profiles)["risk"]["status"],"blocked")


if __name__=="__main__":
    unittest.main()
