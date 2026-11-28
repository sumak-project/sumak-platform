"""Static safety checks for the reusable service Helm chart.

These checks intentionally do not substitute for Helm rendering or a cluster
schema/runtime validation.
"""
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHART = ROOT / "infra/helm/service"
VALUES_PATH = CHART / "values.yaml"
DEV_VALUES_PATH = ROOT / "config/dev/base-service-values.yaml"


def read(path):
    return path.read_text(encoding="utf-8")


def scalar(values, key):
    match = re.search(rf"(?m)^{re.escape(key)}:\s*(.*?)\s*$", values)
    if not match:
        raise AssertionError(f"Missing YAML scalar {key}")
    return match.group(1).strip().strip("\"'")


def yaml_block(text, key, parent_indent=-2):
    """Return one direct YAML mapping block, bounded by the next sibling."""
    lines = text.splitlines()
    key_indent = parent_indent + 2
    for index, line in enumerate(lines):
        if line.startswith(" " * key_indent + key + ":"):
            block = [line]
            for following in lines[index + 1 :]:
                if following.strip() and len(following) - len(following.lstrip()) <= key_indent:
                    break
                block.append(following)
            return "\n".join(block)
    raise AssertionError(f"Missing YAML block {key}")


class BaseServiceHelmChartTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.values = read(VALUES_PATH)
        cls.dev_values = read(DEV_VALUES_PATH)
        cls.schema = json.loads(read(CHART / "values.schema.json"))
        cls.deployment = read(CHART / "templates/deployment.yaml")

    def test_chart_and_schema_structure(self):
        chart = read(CHART / "Chart.yaml")
        self.assertIn("apiVersion: v2", chart)
        self.assertIn("name: sumak-service", chart)
        self.assertRegex(chart, r'(?m)^kubeVersion:\s*">=1\.32\.0-0 <1\.38\.0-0"$')
        self.assertEqual(self.schema["properties"]["replicaCount"]["maximum"], 3)
        self.assertEqual(self.schema["properties"]["replicaCount"]["minimum"], 1)
        self.assertEqual(
            self.schema["properties"]["image"]["properties"]["digest"]["pattern"],
            "^sha256:[a-fA-F0-9]{64}$",
        )

    def test_kubernetes_version_bounds_are_inclusive_132_through_137(self):
        constraint = re.search(r'(?m)^kubeVersion:\s*"([^"]+)"', read(CHART / "Chart.yaml"))
        self.assertIsNotNone(constraint)
        minimum, maximum = re.fullmatch(r">=1\.(\d+)\.0-0 <1\.(\d+)\.0-0", constraint.group(1)).groups()
        minimum, maximum = int(minimum), int(maximum)
        self.assertEqual((minimum, maximum), (32, 38))
        self.assertTrue(all(minimum <= minor < maximum for minor in range(32, 38)))
        self.assertFalse(minimum <= 31 < maximum)
        self.assertFalse(minimum <= 38 < maximum)
        self.assertEqual(
            set(self.schema["properties"]["probes"]["properties"]),
            {"liveness", "readiness", "startup"},
        )

    def test_all_three_probes_are_enabled_and_rendered(self):
        for probe, path in (
            ("liveness", "/health/live"),
            ("readiness", "/health/ready"),
            ("startup", "/health/startup"),
        ):
            block = yaml_block(yaml_block(self.values, "probes"), probe, parent_indent=0)
            self.assertRegex(block, r"(?m)^\s+enabled: true$")
            self.assertIn(f"path: {path}", block)
            self.assertIn(f".Values.probes.{probe}.enabled", self.deployment)
            self.assertIn(f".Values.probes.{probe}.path", self.deployment)

    def test_resource_budgets_and_security_defaults(self):
        for line in ("cpu: 100m", "memory: 256Mi", "cpu: 500m", "memory: 512Mi"):
            self.assertIn(line, self.values)
        self.assertRegex(self.values, r"(?ms)^podSecurityContext:\s*\n\s+runAsNonRoot: true")
        self.assertIn("type: RuntimeDefault", self.values)
        for security_default in (
            "allowPrivilegeEscalation: false",
            "readOnlyRootFilesystem: true",
            "runAsNonRoot: true",
            "runAsUser: 10001",
            "- ALL",
        ):
            self.assertIn(security_default, self.values)
        self.assertIn("automount: false", self.values)

    def test_digest_only_image_no_secret_literals_and_dev_only_example(self):
        self.assertIn('{{ .Values.image.repository }}@{{ .Values.image.digest }}', self.deployment)
        self.assertNotRegex(self.values + self.dev_values, r"(?i)(?:^|\s)tag:\s*")
        self.assertNotRegex(self.values + self.dev_values, r"(?i)latest")
        self.assertNotRegex(
            self.values + self.dev_values,
            r"(?i)(?:password|token|secret)\s*:\s*[\"']?(?!$|\"|')\S+",
        )
        self.assertIn("DEV-only example", self.dev_values)
        self.assertEqual(scalar(self.dev_values, "replicaCount"), "1")
        image_block = yaml_block(self.dev_values, "image")
        digest_match = re.search(r"(?m)^\s+digest:\s*(\S+)\s*$", image_block)
        self.assertIsNotNone(digest_match)
        self.assertRegex(digest_match.group(1), r"^sha256:[a-fA-F0-9]{64}$")


if __name__ == "__main__":
    unittest.main()
