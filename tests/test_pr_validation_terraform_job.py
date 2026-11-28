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
        terraform_job = re.search(
            r"(?ms)^  terraform:\s*\n(.*?)(?=^  [A-Za-z0-9_-]+:\s*$|\Z)",
            cls.jobs,
        )
        if terraform_job is None:
            raise AssertionError("Terraform validation job must exist")
        cls.terraform_steps = named_step_blocks(terraform_job.group(1))

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
        self.assertRegex(self.source, r"(?m)^\s{2}changes:\s*$")
        self.assertRegex(self.source, r"(?m)^\s+terraform_changed:\s*\$\{\{\s*steps\.route\.outputs\.terraform_changed\s*\}\}")
        detector = (WORKFLOW.parent.parent.parent / "scripts/ci/detect_changes.py").read_text()
        self.assertIn('path.startswith(("infra/accounts/", "infra/modules/"))', detector)
        self.assertIn('path.endswith(".tf")', detector)
        terraform_condition = (
            r"needs\.changes\.result == 'success' && "
            r"needs\.changes\.outputs\.terraform_changed == 'true'"
        )
        terraform_only = (
            "Check out the reviewed commit",
            "Set up Terraform",
            "Prepare isolated Terraform cache",
            "Check Terraform formatting",
            "Initialize and validate Terraform roots",
            "Scan Terraform security and policy",
            "Create reviewed Terraform plans",
            "Upload limited-retention Terraform plans",
        )
        terraform_blocks = {name: self.terraform_steps[name] for name in terraform_only}
        for block in terraform_blocks.values():
            self.assertRegex(block, rf"(?m)^\s+if:\s*{terraform_condition}\s*$")

        for value in ("true", "false"):
            scheduled = {
                name for name, block in terraform_blocks.items()
                if re.search(
                    rf"(?m)^\s+if:\s*{terraform_condition}\s*$", block
                ) and value == "true"
            }
            self.assertEqual(scheduled, set(terraform_only) if value == "true" else set())

    def test_routing_failure_still_schedules_required_jobs_and_blocks(self):
        for job in ("terraform", "validate"):
            block = re.search(
                rf"(?ms)^  {job}:\s*\n(.*?)(?=^  [A-Za-z0-9_-]+:\s*$|\Z)",
                self.jobs,
            )
            self.assertIsNotNone(block)
            assert block is not None
            self.assertRegex(block.group(1), r"(?m)^\s+if:\s*always\(\)\s*$")

        terraform_assertion = self.terraform_steps["Require a resolved Terraform routing decision"]
        validation_assertion = self.steps["Require a resolved validation routing decision"]
        self.assertRegex(terraform_assertion, r"(?m)^\s+if:\s*always\(\)\s*$")
        self.assertRegex(validation_assertion, r"(?m)^\s+if:\s*always\(\)\s*$")
        self.assertIn('if [[ "$ROUTING_RESULT" != "success"', terraform_assertion)
        self.assertIn('if [[ "$ROUTING_RESULT" != "success"', validation_assertion)
        self.assertIn("BLOCKED: Terraform checks require", terraform_assertion)
        self.assertIn("BLOCKED: validation did not receive", validation_assertion)
        self.assertIn(
            "did not receive successful, explicit path-routing decisions",
            validation_assertion,
        )
        for routed_step in ("Run deterministic contract checks", "Check Gradle project"):
            self.assertIn(
                "needs.changes.result == 'success'",
                self.steps[routed_step],
                f"{routed_step} must not run if routing failed, even if it emitted outputs",
            )

        # General validation is checked separately from path-gated work, so a
        # failed route does not skip checkout, wrapper validation, PR metadata,
        # or policy tests before its explicit BLOCKED assertion.
        for required in (
            "Validate Gradle wrapper",
            "Validate branch name and PR title",
            "Test quality gate policy",
        ):
            self.assertIn(required, self.steps)
        self.assertNotRegex(
            self.steps["Validate Gradle wrapper"], r"(?m)^\s+if:"
        )
        self.assertNotRegex(
            self.steps["Validate branch name and PR title"], r"(?m)^\s+if:"
        )
        self.assertNotRegex(
            self.steps["Test quality gate policy"], r"(?m)^\s+if:"
        )

    def test_missing_or_non_boolean_routing_outputs_cannot_succeed(self):
        terraform_assertion = self.terraform_steps["Require a resolved Terraform routing decision"]
        self.assertIn(
            'if [[ "$ROUTING_RESULT" != "success" || ! "$TERRAFORM_CHANGED" =~ ^(true|false)$ ]]; then',
            terraform_assertion,
        )
        validation_assertion = self.steps["Require a resolved validation routing decision"]
        self.assertIn('if [[ "$ROUTING_RESULT" != "success"', validation_assertion)
        self.assertIn('|| ! "$CONTRACT_CHANGED" =~ ^(true|false)$', validation_assertion)
        self.assertIn('|| ! "$GRADLE_CHANGED" =~ ^(true|false)$', validation_assertion)
        for output_var in ("CONTRACT_CHANGED", "GRADLE_CHANGED"):
            output_binding = f"{output_var}: ${{{{ needs.changes.outputs."
            self.assertIn(output_binding, validation_assertion)
        self.assertIn(
            'if [[ "$CONTRACT_CHANGED" == "true" && "$CONTRACT_CHECK_OUTCOME" != "success" ]]',
            validation_assertion,
        )
        self.assertIn(
            'if [[ "$CONTRACT_CHANGED" == "false" && "$CONTRACT_CHECK_OUTCOME" != "skipped" ]]',
            validation_assertion,
        )
        self.assertIn(
            'if [[ "$GRADLE_CHANGED" == "true" && "$GRADLE_CHECK_OUTCOME" != "success" ]]',
            validation_assertion,
        )
        self.assertIn(
            'if [[ "$GRADLE_CHANGED" == "false" && "$GRADLE_CHECK_OUTCOME" != "skipped" ]]',
            validation_assertion,
        )
        self.assertIn("CONTRACT_CHECK_OUTCOME: ${{ steps.contract_checks.outcome }}", validation_assertion)
        self.assertIn("GRADLE_CHECK_OUTCOME: ${{ steps.gradle_checks.outcome }}", validation_assertion)
        for name, expected in (
            ("Run deterministic contract checks", "contract_changed"),
            ("Check Gradle project", "gradle_changed"),
        ):
            block = self.steps[name]
            self.assertRegex(
                block,
                rf"(?m)^\s+if:\s*needs\.changes\.result == 'success' && needs\.changes\.outputs\.{expected} == 'true'$",
            )
        self.assertRegex(terraform_assertion, r"(?m)^\s+exit 1\s*$")
        self.assertRegex(validation_assertion, r"(?m)^\s+exit 1\s*$")
        boolean_output = re.compile(r"^(true|false)$")
        for absent_or_invalid in ("", "TRUE", "yes", "0"):
            with self.subTest(output=absent_or_invalid):
                self.assertIsNone(boolean_output.fullmatch(absent_or_invalid))
        self.assertIsNotNone(boolean_output.fullmatch("false"))

    def test_offline_terraform_gates_remain_unconditional_and_fail_closed(self):
        for name in (
            "Check Terraform formatting",
            "Initialize and validate Terraform roots",
            "Scan Terraform security and policy",
        ):
            self.assertRegex(
                self.terraform_steps[name],
                r"(?m)^\s+if:\s*needs\.changes\.result == 'success' && needs\.changes\.outputs\.terraform_changed == 'true'$",
            )
        self.assertRegex(self.source, r"(?m)^\s*continue-on-error:\s*false\s*$")


if __name__ == "__main__":
    unittest.main()
