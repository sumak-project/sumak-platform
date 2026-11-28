"""Contract package regression tests; no generated evidence is rewritten."""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import common


class PackageTests(unittest.TestCase):
    def test_catalog_is_deterministic_current_and_pending(self):
        catalog = common.generate(check=True)
        self.assertEqual(162, catalog["rowCount"])
        self.assertEqual(162, catalog["pendingCount"])
        self.assertEqual(0, catalog["generatedCount"])
        self.assertEqual(common.catalog_bytes(catalog),
                         common.GENERATED_PATH.read_bytes())
        self.assertTrue(all(row["generationResult"] == "PENDING"
                            for row in catalog["entries"]))
        schema_suffixes = {".graphqls", ".proto", ".yaml", ".yml"}
        self.assertFalse(any(path.is_file() and path.suffix in schema_suffixes
                             for path in ROOT.rglob("*")))

    def test_policy_protocol_split_and_reviewed_matrix_digest(self):
        policy = common.load_json(common.POLICY_PATH)
        common.validate_policy(policy)
        self.assertEqual(common.PROTOCOLS, policy["protocols"])
        matrix = common.load_json(common.MATRIX_PATH)
        baseline = common.load_json(common.BASELINE_PATH)
        self.assertEqual(matrix["contentSha256"], baseline["approvedMatrixSha256"])
        self.assertEqual({}, baseline["contracts"])

    def test_stale_output_and_matrix_digest_drift_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            stale = Path(directory) / "catalog.json"
            stale.write_text("{}")
            with patch.object(common, "GENERATED_PATH", stale):
                with self.assertRaisesRegex(common.ContractPackageError, "stale"):
                    common.generate(check=True)
            self.assertEqual("{}", stale.read_text())

        matrix = common.load_json(common.MATRIX_PATH)
        baseline = common.load_json(common.BASELINE_PATH)
        baseline["approvedMatrixSha256"] = "0" * 64
        with patch.object(common, "load_json", side_effect=[matrix, baseline]), \
                patch.object(common, "generate", return_value={
                    "entries": [], "pendingCount": 162,
                }):
            with self.assertRaisesRegex(common.ContractPackageError, "digest changed"):
                common.check_compatibility()


if __name__ == "__main__":
    unittest.main()
