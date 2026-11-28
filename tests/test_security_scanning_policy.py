#!/usr/bin/env python3
"""Fail-closed policy checks for the dedicated security-scanning workflow."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/security-scanning.yml"


class SecurityScanningPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not WORKFLOW.exists():
            raise AssertionError(f"Security workflow is not implemented yet: {WORKFLOW}")
        cls.source = WORKFLOW.read_text(encoding="utf-8")

    def test_pr_to_dev_only_with_minimal_permissions_and_three_separate_jobs(self):
        source = self.source
        self.assertRegex(source, r"(?m)^on:\s*$")
        self.assertRegex(source, r"(?ms)^on:\s*\n(?:(?!^[^\s]).*\n)*?\s+pull_request:\s*")
        self.assertRegex(source, r"(?m)^\s{6}branches:\s*\n\s{8}-\s*dev\s*$")
        self.assertRegex(source, r"(?m)^permissions:\s*$")
        self.assertRegex(source, r"(?m)^\s{2}contents:\s*read\s*$")
        self.assertRegex(source, r"(?m)^\s{2}pull-requests:\s*read\s*$")
        for job in ("dependency-review", "secret-scan", "source-security"):
            self.assertRegex(source, rf"(?m)^\s{{2}}{job}:\s*$")

    def test_actions_and_scanner_versions_are_pinned(self):
        references = re.findall(r"(?m)^\s*uses:\s*([^\s#]+)", self.source)
        self.assertTrue(references, "Workflow must use pinned actions")
        for reference in references:
            if reference.startswith("./"):
                continue
            self.assertRegex(
                reference,
                r"^[^@]+@(?:[0-9a-f]{40}|v?\d+\.\d+\.\d+(?:[-+][A-Za-z0-9.-]+)?)$",
                f"Action reference must be immutable/pinned: {reference}",
            )
        self.assertNotRegex(self.source, r"(?i)dependency-review-action")
        self.assertRegex(self.source, r"(?i)trivy")
        self.assertRegex(self.source, r"(?m)^\s*scan-type:\s*rootfs\s*$")
        self.assertRegex(self.source, r"(?i)gitleaks")
        self.assertRegex(self.source, r"(?i)semgrep")
        self.assertRegex(self.source, r"(?i)zizmor")

    def test_fail_closed_severity_coverage_and_pr_range_are_explicit(self):
        source = self.source.lower()
        self.assertRegex(source, r"(?i)GRADLE_USER_HOME")
        self.assertRegex(source, r"(?i)(gradle.*dependencies|dependencies.*gradle)")
        self.assertRegex(source, r"(?i)(vuln|vulnerability)")
        self.assertRegex(source, r"(?i)HIGH,?\s*CRITICAL")
        self.assertRegex(source, r"(?i)(--exit-code\s+1|exit-code:\s*[\"']?1)")
        self.assertRegex(source, r"(?i)gradle")
        self.assertRegex(source, r"(?i)caches/modules-2/files-2.1")
        self.assertRegex(source, r"(?i)(dependency.*input|gradle.*input)")
        self.assertRegex(source, r"(?i)fetch-depth:\s*0")
        self.assertRegex(source, r"(?i)base.sha")
        self.assertRegex(source, r"(?i)head.sha")
        self.assertRegex(source, r"(?i)(git diff|changed)")
        self.assertRegex(source, r"(?i)no reviewed gradle dependency inputs changed")
        self.assertRegex(source, r"(?i)(--redact|redact)")
        self.assertRegex(source, r"(?i)(full history|fetch-depth:\s*0|base_ref|head_ref)")
        self.assertRegex(source, r"(?i)(--error|error)")
        self.assertRegex(source, r"(?i)(continue-on-error:\s*false|set -e)")

    def test_dependency_resolve_and_rootfs_scan_use_centralized_safe_detector(self):
        source = self.source
        self.assertRegex(source, r"(?m)^\s+fetch-depth:\s*0\s*$")
        self.assertRegex(source, r"(?m)^\s+BASE_SHA:\s*\$\{\{\s*github\.event\.pull_request\.base\.sha\s*\}\}")
        self.assertRegex(source, r"(?m)^\s+HEAD_SHA:\s*\$\{\{\s*github\.event\.pull_request\.head\.sha\s*\}\}")
        self.assertIn("scripts/ci/detect_changes.py", source)
        self.assertIn("gradle_dependency_inputs_changed", source)
        detector = ROOT / "scripts/ci/detect_changes.py"
        implementation = detector.read_text(encoding="utf-8")
        self.assertIn("GRADLE_SHARED_INPUTS", implementation)
        self.assertIn('name.endswith((".gradle", ".gradle.kts"))', implementation)
        self.assertIn('"gradle/wrapper/"', implementation)
        self.assertIn('"/gradle/dependency-locks/"', implementation)
        self.assertIn('"gradle/libs.versions.toml"', implementation)
        steps = re.split(r"(?m)^\s{6}- name:", source)
        for fragment in steps:
            if re.search(r"(?i)(resolve reviewed gradle dependencies|reject high or critical dependency vulnerabilities)", fragment):
                self.assertRegex(fragment, r"(?m)^\s+if:\s*steps\.dependency-changes\.outputs\.gradle_dependency_inputs_changed\s*==\s*['\"]true['\"]")
        self.assertRegex(source, r"(?i)no reviewed gradle dependency inputs changed")
        self.assertNotRegex(source, r"(?i)dependency-review-action")

    def test_no_credentials_or_silent_waivers_and_waiver_has_owner_and_adr(self):
        source = self.source
        self.assertNotRegex(source, r"(?i)\b(AWS_ACCESS_KEY_ID|AWS_SECRET_ACCESS_KEY|secrets\.AWS)")
        self.assertNotRegex(source, r"(?i)continue-on-error:\s*true")
        self.assertNotRegex(source, r"(?i)(allowlist|allow-list|exclude-paths|skip.*secret)")
        self.assertRegex(source, r"(?i)owner")
        self.assertRegex(source, r"(?i)(justification|rationale)")
        self.assertRegex(source, r"(?i)ADR")
        self.assertRegex(source, r"(?i)(^|[\s(])docs/|architecture/decisions/")

    def test_synthetic_marker_fixture_is_created_outside_repository(self):
        # This verifies fixture isolation only; scanner detection is validated separately.
        with __import__("tempfile").TemporaryDirectory() as directory:
            fixture = Path(directory) / "synthetic-fixture.txt"
            fixture.write_text("synthetic-test-marker-not-a-secret\n", encoding="utf-8")
            self.assertIn("synthetic-test-marker-not-a-secret", fixture.read_text(encoding="utf-8"))
            self.assertFalse(fixture.is_relative_to(ROOT))


if __name__ == "__main__":
    unittest.main()
