"""Contract checks for the candidate API migration matrix catalog."""

import importlib.util
import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "contracts/catalog/api-migration"
GENERATOR = CATALOG / "generate_matrix.py"
SPEC = importlib.util.spec_from_file_location("api_migration_matrix", GENERATOR)
matrix = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = matrix
SPEC.loader.exec_module(matrix)


class ApiMigrationMatrixTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = json.loads(
            (CATALOG / "api-migration-matrix.json").read_text(encoding="utf-8")
        )

    def test_catalog_has_162_unique_v1_routes_and_expected_surfaces(self):
        routes = matrix._load_routes()
        matrix._validate_sources(routes, matrix._load_overrides())
        keys = [row["SOURCE_METHOD_PATH"] for row in routes]
        self.assertEqual(162, len(keys))
        self.assertEqual(162, len(set(keys)))
        self.assertEqual(
            {"mobile": 55, "admin": 87, "public": 15, "integration": 5},
            dict(matrix._validate_sources(routes, matrix._load_overrides())),
        )
        self.assertTrue(all(key.split()[1].startswith("/v1/") for key in keys))

    def test_generated_contract_and_evidence_are_conservative(self):
        document = self.document
        self.assertEqual(16, len(matrix.FIELDS))
        self.assertEqual(list(matrix.FIELDS), document["columns"])
        self.assertEqual("PENDING", document["approval"])
        self.assertEqual("CANDIDATE_PARTIAL", document["classification"])
        self.assertEqual(
            "Candidate input; never executable output.",
            document["sourcePolicy"]["historicalRestInventory"],
        )
        self.assertEqual(162, document["rowCount"])
        self.assertEqual({"mobile": 55, "admin": 87, "public": 15, "integration": 5},
                         document["surfaceCounts"])
        matrix._validate_matrix(document)

    def test_generated_files_are_deterministic_and_current(self):
        result = subprocess.run(
            [sys.executable, str(GENERATOR), "--check"],
            cwd=ROOT, text=True, capture_output=True,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        routes = matrix._load_routes()
        built = matrix._build_matrix(routes, matrix._load_overrides())
        self.assertEqual(
            (CATALOG / "api-migration-matrix.json").read_bytes(),
            matrix._json_bytes(built),
        )
        self.assertEqual(
            (CATALOG / "api-migration-matrix.csv").read_bytes(),
            matrix._csv_bytes(built),
        )

    def test_source_and_override_errors_fail_closed(self):
        routes = matrix._load_routes()
        overrides = matrix._load_overrides()
        cases = [
            (routes + [routes[0]], overrides),
            ([{**routes[0], "SOURCE_METHOD_PATH": "GET /v1/unknown/x"}] + routes[1:],
             overrides),
            (routes, {**overrides, "GET /v1/mobile/not-a-route": {}}),
            (routes, {routes[0]["SOURCE_METHOD_PATH"]: {"NOT_A_FIELD": {}}}),
            (routes, {routes[0]["SOURCE_METHOD_PATH"]: {
                "BUSINESS_INTENT": {"value": "x", "source": "fixture",
                                    "status": "INVALID", "note": "fixture"}
            }}),
        ]
        for source_routes, source_overrides in cases:
            with self.subTest(routes=len(source_routes), overrides=source_overrides):
                with self.assertRaises(matrix.MatrixError):
                    matrix._validate_sources(source_routes, source_overrides)

    def test_cli_rejects_malformed_fixture_without_touching_catalog(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory) / "source-routes.tsv"
            fixture.write_text("SOURCE_METHOD_PATH\tOWNER\nGET /v1/mobile/x\towner\n",
                               encoding="utf-8")
            with self.assertRaises(matrix.MatrixError):
                with fixture.open(encoding="utf-8", newline="") as stream:
                    rows = list(csv.DictReader(stream, delimiter="\t"))
                matrix._validate_sources(rows, {})


if __name__ == "__main__":
    unittest.main()
