"""Static checks for the API gateway's DEV values and shared chart contract."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALUES = ROOT / "config/dev/api-gateway-values.yaml"
CHART = ROOT / "infra/helm/service"


def direct_block(text, key, indent=0):
    lines = text.splitlines()
    prefix = " " * indent + key + ":"
    for index, line in enumerate(lines):
        if line.startswith(prefix):
            result = [line]
            for subsequent in lines[index + 1:]:
                if subsequent.strip() and len(subsequent) - len(subsequent.lstrip()) <= indent:
                    break
                result.append(subsequent)
            return "\n".join(result)
    raise AssertionError(f"Missing block {key}")


class ApiGatewayDevValuesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.values = VALUES.read_text(encoding="utf-8")
        cls.chart_defaults = (CHART / "values.yaml").read_text(encoding="utf-8")
        cls.schema = json.loads((CHART / "values.schema.json").read_text(encoding="utf-8"))

    def test_values_match_shared_chart_schema_and_private_service(self):
        self.assertTrue((CHART / "Chart.yaml").is_file())
        self.assertEqual(self.schema["properties"]["service"]["properties"]["type"]["enum"], ["ClusterIP"])
        service = direct_block(self.values, "service")
        self.assertRegex(service, r"(?m)^\s+type:\s*ClusterIP\s*$")
        self.assertRegex(service, r"(?m)^\s+port:\s*8080\s*$")
        self.assertNotRegex(self.values, r"(?im)^\s*(?:ingress|loadBalancer):")

    def test_probe_paths_and_explicit_budgets_follow_chart_values(self):
        for probe, path in (("liveness", "/health/live"), ("readiness", "/health/ready"), ("startup", "/health/startup")):
            block = direct_block(self.values, probe, indent=2)
            self.assertRegex(block, r"(?m)^\s+enabled:\s*true\s*$")
            self.assertRegex(block, rf"(?m)^\s+path:\s*{re.escape(path)}\s*$")
            self.assertRegex(block, r"(?m)^\s+port:\s*http\s*$")
        resources = direct_block(self.values, "resources")
        for budget in ("cpu: 100m", "memory: 256Mi", "cpu: 500m", "memory: 512Mi"):
            self.assertIn(budget, resources)
        template = (CHART / "templates/deployment.yaml").read_text(encoding="utf-8")
        for name in ("liveness", "readiness", "startup"):
            self.assertIn(f".Values.probes.{name}.path", template)

    def test_digest_is_immutable_placeholder_and_dev_only(self):
        image = direct_block(self.values, "image")
        self.assertRegex(image, r"(?m)^\s+digest:\s*sha256:[a-fA-F0-9]{64}\s*$")
        self.assertIn("example.invalid", image)
        self.assertIn("placeholder", self.values.lower())
        self.assertEqual(direct_block(self.values, "replicaCount").split(":", 1)[1].strip(), "1")
        self.assertNotRegex(self.values, r"(?im)^\s*tag:")

    def test_chart_default_probe_contract_contains_all_gateway_paths(self):
        for path in ("/health/live", "/health/ready", "/health/startup"):
            self.assertIn(path, self.chart_defaults)
        self.assertEqual(set(self.schema["properties"]["probes"]["properties"]), {"liveness", "readiness", "startup"})


if __name__ == "__main__":
    unittest.main()
