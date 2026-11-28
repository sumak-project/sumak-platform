"""Static packaging contract checks; these do not build or run an OCI image."""
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SERVICE = ROOT / "services/config-svc"
DOCKERFILE = SERVICE / "Dockerfile"
APPLICATION = SERVICE / "src/main/resources/application.yml"


class ConfigServiceOciContractTest(unittest.TestCase):
    def test_dockerfile_runs_as_non_root_and_exposes_actuator_probes(self):
        self.assertTrue(
            DOCKERFILE.is_file(),
            "config-svc must provide a Dockerfile defining its OCI runtime contract",
        )
        dockerfile = DOCKERFILE.read_text(encoding="utf-8")
        self.assertRegex(
            dockerfile,
            r"(?ms)^FROM\s+\$\{RUNTIME_IMAGE\}\s+AS\s+runtime\s*$"
            r".*?^RUN\s+apk\s+add\s+--no-cache\s+"
            r"zlib=1\.4-r0\s+expat=2\.11\.0-r0\s*$",
            "runtime must install the explicitly pinned, remediated Alpine packages",
        )
        self.assertRegex(dockerfile, r"(?m)^USER\s+(?:10001(?::10001)?|[A-Za-z_][\w.-]*)\s*$")
        self.assertRegex(dockerfile, r"(?m)^HEALTHCHECK\s+(?!NONE\b).+")
        for endpoint in ("/health/live", "/health/ready", "/health/startup"):
            self.assertIn(endpoint, dockerfile)

    def test_actuator_exposes_health_groups_and_probe_paths(self):
        application = APPLICATION.read_text(encoding="utf-8")
        self.assertRegex(application, r"(?m)^\s+include:\s*['\"]?health(?:,\s*info)?['\"]?\s*$")
        self.assertRegex(application, r"(?m)^\s+base-path:\s*/\s*$")
        self.assertRegex(application, r"(?m)^\s+path-mapping:\s*$")
        self.assertRegex(application, r"(?m)^\s+health:\s*health\s*$")
        self.assertRegex(application, r"(?m)^\s+group:\s*$")
        for group in ("live", "ready", "startup"):
            group_block = re.search(
                rf"(?ms)^\s+{group}:\s*\n((?:^\s+.*\n)*)", application
            )
            self.assertIsNotNone(group_block, f"Missing health group {group}")


if __name__ == "__main__":
    unittest.main()
