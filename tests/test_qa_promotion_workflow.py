#!/usr/bin/env python3
"""Policy tests for bounded, PR-based DEV-to-QA promotion orchestration."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/qa-promotion-gate.yml"


class QaPromotionWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = WORKFLOW.read_text(encoding="utf-8")
        cls.lower = cls.source.lower()

    def test_only_pull_requests_targeting_qa_trigger_the_workflow(self):
        trigger = re.search(r"(?ms)^on:\s*\n(.*?)(?=^[^\s]|\Z)", self.source)
        self.assertIsNotNone(trigger, "workflow trigger block must exist")
        block = trigger.group(1)
        self.assertRegex(block, r"(?m)^\s+pull_request:\s*$")
        self.assertRegex(block, r"(?m)^\s+branches:\s*\n\s+-\s+qa\s*$")
        self.assertNotRegex(block, r"(?m)^\s*(?:push|workflow_dispatch|workflow_call|schedule):")

    def test_serialization_and_stale_promotion_guards_are_explicit(self):
        self.assertRegex(self.source, r"(?m)^concurrency:\s*$")
        self.assertRegex(self.source, r"(?i)cancel-in-progress:\s*false")
        self.assertRegex(self.lower, r"(stale|current).{0,120}(promotion|commit|sha)|(promotion|commit|sha).{0,120}(stale|current)")
        self.assertRegex(self.lower, r"\bdev\b")
        self.assertRegex(self.lower, r"(head\.ref|head\.sha|head_ref|head_sha)")

    def test_gate_validation_precedes_protected_owner_approval_and_merge_eligibility(self):
        gate = self.source.find("mandatory-quality-gates:")
        approval = self.source.find("manual-qa-approval:")
        self.assertGreaterEqual(gate, 0)
        self.assertGreater(approval, gate, "approval job must follow gate job")
        approval_block = self.source[approval:]
        self.assertRegex(approval_block, r"(?m)^\s+needs:\s*mandatory-quality-gates\s*$")
        self.assertRegex(approval_block, r"(?m)^\s+environment:\s*qa-promotion-approval\s*$")
        self.assertRegex(self.lower, r"(merge|promotion).{0,160}(eligible|approved|approval)")

    def test_evidence_artifact_is_named_for_exact_commit_and_pr_metadata_is_bound(self):
        self.assertRegex(
            self.lower,
            r"(artifact|upload-artifact).{0,300}(commit|sha).{0,100}(name|path)|(name|path).{0,100}(commit|sha)",
        )
        self.assertRegex(self.lower, r"head\.sha|head_sha")
        self.assertRegex(self.lower, r"head\.ref|head_ref")
        self.assertRegex(self.lower, r"base\.ref|base_ref")
        self.assertRegex(self.lower, r"pull_request")
        self.assertRegex(self.lower, r"(expected|current|github\.sha).{0,120}(commit|sha)|(commit|sha).{0,120}(expected|current|github\.sha)")

    def test_post_approval_rechecks_current_dev_and_qa_tips(self):
        approval = self.source[self.source.find("manual-qa-approval:"):]
        recheck = approval.find("Recheck current branches after owner approval")
        self.assertGreaterEqual(recheck, 0)
        block = approval[recheck:]
        self.assertRegex(block, r"(?s)current_dev_sha=.*?git/ref/heads/dev")
        self.assertRegex(block, r"(?s)current_qa_sha=.*?git/ref/heads/qa")
        self.assertRegex(block, r"APPROVED_HEAD_SHA.*current_dev_sha")
        self.assertRegex(block, r"APPROVED_BASE_SHA.*current_qa_sha")

    def test_ambiguous_or_expired_exact_sha_artifacts_fail_closed(self):
        download = self.source[self.source.find("Download exact-SHA quality-gate evidence"):
                               self.source.find("Validate exact promotion evidence")]
        self.assertRegex(download, r"(?i)expired\s*==\s*false")
        self.assertRegex(download, r"workflow_run\.head_sha\s*==\s*\$sha")
        self.assertRegex(download, r"\$\{#artifact_rows\[@\]\}\s*!=\s*1")
        self.assertRegex(download, r"(?i)exactly one non-expired")

    def test_workflow_never_merges_the_pull_request(self):
        self.assertNotRegex(
            self.lower,
            r"\b(?:gh\s+pr\s+merge|git\s+merge|merge-pull-request|merge_method)\b",
        )

    def test_permissions_are_least_privilege_and_workflow_is_non_mutating(self):
        permissions = re.search(r"(?ms)^permissions:\s*\n(.*?)(?=^[^\s]|\Z)", self.source)
        self.assertIsNotNone(permissions)
        self.assertRegex(permissions.group(1), r"(?m)^\s+contents:\s+read\s*$")
        self.assertNotRegex(permissions.group(1), r"(?m)^\s+[a-z_-]+:\s+write\s*$")
        forbidden = (
            r"\b(?:git\s+push|gh\s+api.*(?:protection|deploy)|aws\s+(?:eks|ecr|cloudformation|s3|ssm)|"
            r"kubectl\s+(?:apply|delete)|helm\s+(?:upgrade|install|uninstall)|"
            r"(?:branch[- ]protection|qa.?to.?prod|smoke.?test))\b"
        )
        self.assertNotRegex(self.lower, forbidden)


if __name__ == "__main__":
    unittest.main()
