#!/usr/bin/env python3
"""Fail-closed static policy checks for manual DEV Helm deployment."""
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/dev-helm-deploy.yml"


class DevHelmDeployWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = WORKFLOW.read_text(encoding="utf-8")
        cls.lower = cls.source.lower()

    def test_manual_authorization_environment_and_serialized_concurrency(self):
        self.assertRegex(self.source, r"(?ms)^on:\s*\n\s+workflow_dispatch:")
        self.assertIn("DEPLOY-DEV", self.source)
        self.assertNotRegex(self.source, r"(?m)^\s*(?:push|pull_request|schedule|workflow_run):")
        self.assertRegex(self.source, r"(?m)^\s+environment:\s*dev\s*$")
        self.assertRegex(self.source, r"(?m)^\s+cancel-in-progress:\s*false\s*$")
        self.assertRegex(self.source, r"(?m)^\s+group:\s*\S+")

    def test_digest_account_repository_and_config_svc_are_fixed_and_validated(self):
        self.assertRegex(self.source, r"\^sha256:\[0-9a-f\]\{64\}\$")
        self.assertIn("632080579751", self.source)
        self.assertIn("sumak/dev/config-svc", self.source)
        self.assertRegex(self.source, r"(?i)aws sts get-caller-identity")
        self.assertRegex(self.source, r"(?i)aws ecr describe-images")
        self.assertRegex(self.source, r"(?i)config-svc")
        self.assertRegex(self.source, r"(?i)image\.digest=\$IMAGE_DIGEST")

    def test_namespace_bounded_timeouts_secret_references_and_probes(self):
        self.assertRegex(self.source, r"(?m)^\s+KUBE_NAMESPACE:\s*sumak-dev\s*$")
        self.assertRegex(self.source, r"(?m)^\s+timeout-minutes:\s*\d+")
        for maximum in ("--timeout 10m", "--timeout 5m", "--timeout=5m", "--max-time 5"):
            self.assertIn(maximum, self.source)
        for secret in ("SUMAK_DEV_AWS_ACCESS_KEY_ID", "SUMAK_DEV_AWS_SECRET_ACCESS_KEY",
                       "SUMAK_DEV_AWS_SESSION_TOKEN"):
            self.assertIn("${{ secrets." + secret + " }}", self.source)
        for secret in ("SUMAK_DEV_AWS_ACCESS_KEY_ID", "SUMAK_DEV_AWS_SECRET_ACCESS_KEY",
                       "SUMAK_DEV_AWS_SESSION_TOKEN"):
            self.assertNotIn(secret + ":", self.source)
        self.assertIn("/health/ready", self.source)
        self.assertIn("/health/live", self.source)

    def test_atomic_failure_health_rollback_and_forward_fix(self):
        self.assertIn("--atomic", self.source)
        self.assertIn("--cleanup-on-fail", self.source)
        self.assertRegex(self.source, r"(?i)helm rollback")
        self.assertRegex(self.source, r"(?i)helm uninstall")
        self.assertIn("PREVIOUS_REVISION", self.source)
        self.assertRegex(self.lower, r"forward fix.{0,160}(new|newly).{0,80}digest")


if __name__ == "__main__":
    unittest.main()
