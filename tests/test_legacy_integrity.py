"""Portable regression cases for strengthened legacy bundle/input boundaries."""
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import run_research
from market_io import number,records
from legacy_bundle_integrity import verify_snapshot


class LegacyIntegrityTests(unittest.TestCase):
    def test_new_bundle_hashes_report_and_rejects_tamper(self):
        with tempfile.TemporaryDirectory() as temp:
            root=run_research.run(ROOT/"examples/workbench.json",temp)
            self.assertEqual(verify_snapshot(root/"config.snapshot.json"),"hashed_artifacts")
            (root/"REPORT.html").write_text("changed",encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"hash mismatch"):
                run_research.load(root/"config.snapshot.json")

    def test_old_frozen_input_hashes_still_verify(self):
        self.assertEqual(verify_snapshot(ROOT/"examples/workbench/config.snapshot.json"),"legacy_input_hashes_only")

    def test_input_ambiguity_rejected(self):
        with self.assertRaises(ValueError):
            number(True)
        for body in (b"a,a\n1,2",b"a,b\n1",b"a,b\n1,2,3"):
            with self.assertRaises(ValueError):
                records(body,["a"])


if __name__=="__main__":
    unittest.main()
