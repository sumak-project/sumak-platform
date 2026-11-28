"""Regression contract for the fail-closed official compiler guard."""

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/pr-validation.yml"
GUARD = ROOT / "scripts/ci/check_official_contract_compilers.py"


def write_fixture(root, manifest=True, schema=True, manifest_text=None):
    (root / "contracts").mkdir(parents=True, exist_ok=True)
    if manifest:
        (root / "compiler-manifest.json").write_text(
            manifest_text if manifest_text is not None else json.dumps({
                "tools": [{
                    "name": "fixture-compiler",
                    "version": "1.2.3",
                    "command": ["fixture-compiler", "--check"],
                }]
            }),
            encoding="utf-8",
        )
    if schema:
        (root / "contracts/schema.proto").write_text(
            'syntax = "proto3";\npackage fixture;\n', encoding="utf-8"
        )


def invoke_guard(root, *args, commit="a" * 40):
    # The interface is intentionally exercised via its CLI in an isolated root.
    return subprocess.run(
        [sys.executable, str(GUARD), "--root", str(root),
         "--manifest", "compiler-manifest.json", *args],
        cwd=ROOT, text=True, capture_output=True,
        env={**os.environ, "GITHUB_SHA": commit},
    )


class OfficialContractCompilerGateTest(unittest.TestCase):
    def test_deterministic_commands_and_package_tests_are_mapped(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        for command in (
            "contracts/catalog/api-migration/generate_matrix.py --check",
            "contracts/executable/tools/generar.py --check",
            "contracts/executable/tools/integraciones.py",
            "contracts/executable/tools/trazabilidad.py",
            "contracts/executable/tools/compatibilidad.py",
            "contracts/executable/tools/validar.cjs",
            "contracts/executable/tools/revisar_estructura.py",
            "python3 -m unittest discover -s tests",
        ):
            with self.subTest(command=command):
                self.assertIn(command, workflow)

    def test_prerequisites_guard_invocation_and_commit_binding_are_explicit(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertRegex(workflow, r'python-version:\s*["\']3\.(?:1[0-9]|[1-9][0-9])["\']')
        self.assertRegex(workflow, r'node-version:\s*["\'](?:2[0-9]|[3-9][0-9])(?:\.\d+)?["\']')
        self.assertIn("check_official_contract_compilers.py", workflow)
        self.assertIn("GITHUB_SHA", workflow)

    def test_absent_manifest_or_schemas_block_without_modifying_inputs(self):
        cases = (
            ("missing manifest", False, True),
            ("missing schema", True, False),
        )
        for label, manifest, schema in cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                write_fixture(root, manifest=manifest, schema=schema)
                before = {
                    str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
                    for path in root.rglob("*") if path.is_file()
                }
                result = invoke_guard(root)
                self.assertNotEqual(0, result.returncode, result.stdout)
                self.assertIn("BLOCKED_CONTRACT", result.stdout + result.stderr)
                after = {
                    str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
                    for path in root.rglob("*") if path.is_file()
                }
                self.assertEqual(before, after)

    def test_valid_manifest_requires_pinned_versions_commands_and_schema(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root)
            before = {
                path.relative_to(root): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in root.rglob("*") if path.is_file()
            }
            evidence = root / "evidence.json"
            result = invoke_guard(
                root, "--evidence", str(evidence), commit="b" * 40
            )
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertTrue(evidence.is_file())
            document = json.loads(evidence.read_text(encoding="utf-8"))
            self.assertEqual("b" * 40, document.get("sourceCommit"))
            self.assertEqual("PREREQUISITES_VALID", document.get("status"))
            self.assertEqual("NOT_RUN", document.get("compilerExecution"))
            self.assertTrue(document.get("command"))
            self.assertTrue(document.get("toolVersions"))
            encoded_evidence = json.dumps(document)
            self.assertNotIn("PASS", encoded_evidence.upper())
            for secret in ("GITHUB_TOKEN", "password", "secret-value"):
                self.assertNotIn(secret, encoded_evidence)
            after = {
                path.relative_to(root): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in root.rglob("*")
                if path.is_file() and path != evidence
            }
            self.assertEqual(before, after)

    def test_malformed_and_unpinned_manifests_block(self):
        bad_manifests = (
            "{not-json",
            json.dumps({"tools": [{"name": "compiler", "command": ["compiler"]}]}),
            json.dumps({"tools": [{"name": "compiler", "version": "latest",
                                  "command": ["compiler"]}]}),
            json.dumps({"tools": [{"name": "compiler", "version": "1.0.0"}]}),
        )
        for contents in bad_manifests:
            with self.subTest(manifest=contents), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                write_fixture(root, manifest_text=contents)
                manifest = root / "compiler-manifest.json"
                original = manifest.read_bytes()
                result = invoke_guard(root)
                self.assertNotEqual(0, result.returncode)
                self.assertIn("BLOCKED_CONTRACT", result.stdout + result.stderr)
                self.assertEqual(original, manifest.read_bytes())


if __name__ == "__main__":
    unittest.main()
