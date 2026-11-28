#!/usr/bin/env python3
"""Fail-closed policy checks for the manual DEV config-svc ECR publisher."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/dev-ecr-publish.yml"
ACCOUNT_ID = "632080579751"
REGION = "us-east-1"
REPOSITORY = "sumak/dev/config-svc"


class DevEcrPublishWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = WORKFLOW.read_text(encoding="utf-8") if WORKFLOW.is_file() else ""
        cls.lower_source = cls.source.lower()

    def test_workflow_is_manual_and_requires_explicit_authorization(self):
        self.assertRegex(self.source, r"(?m)^on:\s*$")
        self.assertRegex(self.source, r"(?ms)^on:\s*\n(?:(?!^[^\s]).*\n)*?\s+workflow_dispatch:\s*(?:\n|$)")
        self.assertNotRegex(
            self.source,
            r"(?m)^\s*(?:push|pull_request|schedule|workflow_run):",
            "Publishing must not be triggered automatically",
        )
        self.assertRegex(self.lower_source, r"(authorize|authorization|approval|authorized)")
        self.assertRegex(self.lower_source, r"(manual|workflow_dispatch)")

    def test_uses_temporary_credentials_and_checks_expected_account_before_aws_mutations(self):
        source = self.source
        self.assertRegex(source, r"(?i)(AWS_SESSION_TOKEN|aws_session_token)")
        self.assertRegex(source, r"(?i)(AWS_ACCESS_KEY_ID|aws_access_key_id)")
        self.assertRegex(source, r"(?i)(AWS_SECRET_ACCESS_KEY|aws_secret_access_key)")
        self.assertRegex(source, r"(?i)(EXPECTED_AWS_ACCOUNT_ID|expected.account)")
        identity = re.search(r"(?is)aws\s+sts\s+get-caller-identity.*?(?:\n\s*fi|\n\s*exit)", source)
        self.assertIsNotNone(identity, "Must observe AWS identity and enforce the account guard")
        self.assertIn(ACCOUNT_ID, source)
        self.assertRegex(source, r"(?is)(actual_account_id|account_id).{0,300}(EXPECTED_AWS_ACCOUNT_ID|expected)")
        self.assertRegex(source, r"(?i)(RUNNER_TEMP|mktemp)")
        self.assertRegex(source, r"(?i)(rm\s+-f|trap)")
        self.assertNotRegex(self.lower_source, r"(?i)\b(oidc|assume-role|assumerole|labrole)\b")

    def test_build_and_high_critical_scan_gate_precede_push(self):
        source = self.source
        self.assertRegex(source, r"(?i)(services/config-svc|config-svc)")
        self.assertRegex(source, r"(?i)(docker\s+buildx?\s+build|gradle.*boot.?jar|build.*config-svc)")
        self.assertRegex(source, r"(?i)(trivy|ecr.*scan|vulnerability.*scan)")
        self.assertRegex(source, r"(?i)HIGH\s*,\s*CRITICAL")
        self.assertRegex(source, r"(?i)(--exit-code\s+1|exit-code:\s*[\"']?1)")
        scan = re.search(r"(?is)(?:scan|trivy).{0,1500}(?:push|ecr)", source)
        self.assertIsNotNone(scan, "Security scan must gate publishing")
        self.assertRegex(source, r"(?i)(set\s+-euo\s+pipefail|continue-on-error:\s*false)")

    def test_push_is_limited_to_the_expected_dev_account_region_and_repository(self):
        source = self.source
        self.assertIn(ACCOUNT_ID, source)
        self.assertIn(REGION, source)
        self.assertIn(REPOSITORY, source)
        self.assertRegex(source, r"(?i)(aws\s+ecr\s+get-login-password|ecr-login)")
        self.assertRegex(source, r"(?i)(docker\s+push|buildx\s+build.{0,200}--push)")
        self.assertRegex(source, r"(?i)(ecr\.us-east-1\.amazonaws\.com|aws_account_id|ACCOUNT_ID)")
        self.assertNotRegex(self.lower_source, r"(?i)(cross.?account|replication|aws_ecr_repository_policy)")

    def test_destination_digest_is_resolved_and_exact_digest_is_pulled(self):
        source = self.source
        self.assertRegex(source, r"(?i)(describe-images|batch-get-image)")
        self.assertRegex(source, r"(?i)(imageDigest|image_digest|sha256:)")
        self.assertRegex(source, r"(?i)(ecr\.us-east-1\.amazonaws\.com|REPOSITORY)")
        self.assertRegex(source, r"(?i)docker\s+pull")
        self.assertRegex(source, r"(?i)(imageDigest|image_digest|digest).{0,250}sha256|sha256.{0,250}(imageDigest|image_digest|digest)")

    def test_evidence_is_sanitized_and_never_prints_credentials(self):
        source = self.source
        self.assertRegex(source, r"(?i)(GITHUB_STEP_SUMMARY|evidence|digest)")
        self.assertRegex(source, r"(?i)(printf|echo|tee|jq).{0,500}(digest|account|repository|summary|evidence)")
        self.assertRegex(source, r"(?i)(redact|sanitize|credential.?free|without credentials|no credentials)")
        self.assertNotRegex(
            source,
            r"(?im)^\s*(?:echo|printf|cat|tee).*(?:AWS_ACCESS_KEY_ID|AWS_SECRET_ACCESS_KEY|AWS_SESSION_TOKEN)",
            "Credential material must never be emitted to logs or evidence",
        )
        self.assertNotRegex(source, r"(?i)(::add-mask::\$\{\{\s*secrets\.[^}]+\}\}).*(?:echo|printf)")


if __name__ == "__main__":
    unittest.main()
