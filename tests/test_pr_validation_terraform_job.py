#!/usr/bin/env python3
"""Fail-closed static requirements for PR Terraform validation."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


WORKFLOW = Path(__file__).resolve().parents[1] / ".github/workflows/pr-validation.yml"


def named_step_blocks(source: str) -> dict[str, str]:
    """Collect GitHub Actions steps by name, including their run/with configuration."""
    lines = source.splitlines()
    steps: dict[str, str] = {}
    current_name: str | None = None
    current: list[str] = []
    for line in lines:
        match = re.match(r"^\s{6}- name:\s*(.+?)\s*$", line)
        if match:
            if current_name is not None:
                steps[current_name] = "\n".join(current)
            current_name, current = match.group(1).strip("'\""), [line]
        elif current_name is not None:
            if re.match(r"^\s{6}- ", line):
                steps[current_name] = "\n".join(current)
                current_name, current = None, []
            else:
                current.append(line)
    if current_name is not None:
        steps[current_name] = "\n".join(current)
    return steps


class PrValidationTerraformJobTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = WORKFLOW.read_text(encoding="utf-8")
        cls.steps = named_step_blocks(cls.source)
        jobs = re.search(r"(?ms)^jobs:\s*\n(.*)", cls.source)
        if jobs is None:
            raise AssertionError("Workflow must declare jobs")
        cls.jobs = jobs.group(1)

    def test_terraform_checks_are_a_fail_closed_job(self):
        self.assertRegex(self.jobs, r"(?m)^\s{2}terraform:\s*$")
        terraform_job = re.search(
            r"(?ms)^  terraform:\s*\n(.*?)(?=^  [A-Za-z0-9_-]+:\s*$|\Z)",
            self.jobs,
        )
        self.assertIsNotNone(terraform_job, "Terraform validation job must exist")
        assert terraform_job is not None
        self.assertRegex(terraform_job.group(1), r"(?m)^\s*fail-fast:\s*true\s*$")
        self.assertRegex(terraform_job.group(1), r"(?m)^\s*continue-on-error:\s*false\s*$")

    def test_format_and_backend_free_validate(self):
        commands = "\n".join(self.steps.values())
        self.assertRegex(commands, r"(?m)(?:terraform\s+fmt\s+-check|fmt\s+-check)")
        self.assertRegex(commands, r"(?m)terraform(?:\s+-chdir=[^\s]+)?\s+init\b[^\n]*-backend=false")
        self.assertRegex(commands, r"(?m)terraform(?:\s+-chdir=[^\s]+)?\s+validate\b")

    def test_real_security_scanner_runs(self):
        self.assertRegex(
            self.source,
            r"(?i)(?:aquasecurity/trivy-action|checkov|tfsec|trivy\s+config)",
        )

    def test_account_guard_precedes_plan_and_plan_is_not_applied(self):
        steps = list(self.steps.values())
        joined = "\n".join(steps)
        plan_positions = [
            m.start() for m in re.finditer(r"(?m)terraform(?:\s+-chdir=[^\s]+)?\s+plan\b", joined)
        ]
        self.assertTrue(plan_positions, "Terraform plan must be generated for review")
        guard_patterns = (r"aws sts get-caller-identity",)
        guard_positions = [
            m.start() for pattern in guard_patterns
            for m in re.finditer(pattern, joined, re.IGNORECASE)
        ]
        self.assertTrue(guard_positions, "Require an AWS STS identity/account guard")
        self.assertLess(min(guard_positions), min(plan_positions), "Guard must precede plan")
        self.assertNotRegex(joined, r"(?m)terraform\s+apply\b")

    def test_plan_is_written_outside_repository_and_uploaded(self):
        commands = "\n".join(self.steps.values())
        self.assertRegex(commands, r'plan_dir="\$RUNNER_TEMP/terraform-plans"')
        self.assertRegex(commands, r'(?is)terraform(?:\s+-chdir=[^\s]+)?\s+plan\b.*?-out="\$plan_dir/[^"]+\.tfplan"')
        self.assertRegex(commands, r"actions/upload-artifact@")
        self.assertRegex(commands, r"(?m)^\s*path:\s*\$\{\{\s*runner\.temp\s*\}\}/")

    def test_terraform_plan_and_upload_are_gated_by_tf_source_detector(self):
        source = self.source
        self.assertRegex(source, r"(?is)Detect reviewed Terraform source changes")
        self.assertRegex(source, r"(?is)infra/accounts/\*\.tf\|infra/modules/\*\.tf")
        for name in ("Create reviewed Terraform plans", "Upload limited-retention Terraform plans"):
            self.assertRegex(self.steps[name], r"(?m)^\s+if:\s*steps\.terraform-changes\.outputs\.changed == ['\"]true['\"]")

    def test_offline_terraform_gates_remain_unconditional_and_fail_closed(self):
        for name in (
            "Check Terraform formatting",
            "Initialize and validate Terraform roots",
            "Scan Terraform security and policy",
        ):
            self.assertNotRegex(self.steps[name], r"(?m)^\s+if:")
        self.assertRegex(self.source, r"(?m)^\s*continue-on-error:\s*false\s*$")


if __name__ == "__main__":
    unittest.main()
