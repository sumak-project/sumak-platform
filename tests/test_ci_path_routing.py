import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/ci/detect_changes.py"
SPEC = importlib.util.spec_from_file_location("detect_changes", SCRIPT)
detect_changes = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(detect_changes)


class PathRoutingTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.config = self.root / "path-routing.json"
        self.config.write_text(json.dumps({
            "contractSourcePrefixes": ["contracts/protobuf/"],
            "contractConsumers": {
                "contracts/protobuf/identity.proto": [":services:identity"]
            },
        }))
        self.project = self.root / "services/identity"
        self.project.mkdir(parents=True)
        (self.project / "build.gradle").touch()
        self.config_patch = patch.object(detect_changes, "ROUTING_CONFIG", self.config)
        self.config_patch.start()
        self.root_patch = patch.object(detect_changes, "REPOSITORY", self.root)
        self.root_patch.start()

    def tearDown(self):
        self.root_patch.stop()
        self.config_patch.stop()
        self.temp.cleanup()

    def test_direct_gradle_component_source_routes_only_component(self):
        result = detect_changes.route(["services/identity/src/main/Example.java"])
        self.assertEqual(result["gradle_tasks"], ":services:identity:check")

    def test_shared_gradle_input_routes_all_projects(self):
        result = detect_changes.route(["gradle/libs.versions.toml"])
        self.assertEqual(result["gradle_tasks"], "check")
        self.assertEqual(result["gradle_dependency_inputs_changed"], "true")

    def test_recursive_terraform_path_is_detected(self):
        self.assertEqual(
            detect_changes.route(["infra/modules/network/nested/main.tf"])["terraform_changed"],
            "true",
        )

    def test_explicit_contract_mapping_routes_consumer(self):
        result = detect_changes.route(["contracts/protobuf/identity.proto"])
        self.assertEqual(result["gradle_tasks"], ":services:identity:check")
        self.assertEqual(result["blocked"], "false")

    def test_missing_and_invalid_contract_mapping_block(self):
        for source, mapping in (
            ("contracts/protobuf/unmapped.proto", {}),
            ("contracts/protobuf/identity.proto", {
                "contracts/protobuf/identity.proto": [":services:missing"]
            }),
        ):
            self.config.write_text(json.dumps({
                "contractSourcePrefixes": ["contracts/protobuf/"],
                "contractConsumers": mapping,
            }))
            result = detect_changes.route([source])
            self.assertEqual(result["blocked"], "true")
            self.assertIn("BLOCKED:", result["blocked_reason"])

    def test_deleted_file_is_included_by_git_diff_filter(self):
        with patch.object(detect_changes.subprocess, "run") as run:
            run.return_value.stdout = "services/identity/build.gradle\n"
            self.assertEqual(
                detect_changes.changed_paths("base", "head"),
                ["services/identity/build.gradle"],
            )
            command = run.call_args.args[0]
            self.assertIn("--diff-filter=ACMRTD", command)

    def test_workflow_writes_outputs_and_fails_blocked_mapping(self):
        output = self.root / "github-output"
        with patch.object(detect_changes, "changed_paths",
                          return_value=["contracts/protobuf/unmapped.proto"]), \
             patch("sys.argv", ["detect_changes.py", "--base", "base", "--head", "head",
                                "--github-output", str(output)]), \
             patch("sys.stderr"):
            self.assertEqual(detect_changes.main(), 2)
        contents = output.read_text()
        self.assertIn("gradle_tasks=", contents)
        self.assertIn("blocked=true", contents)
        self.assertIn("blocked_reason=BLOCKED:", contents)


if __name__ == "__main__":
    unittest.main()
