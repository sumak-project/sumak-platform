#!/usr/bin/env python3
"""Bounded, dependency-free unittest for the QA promotion validator."""

from __future__ import annotations

import importlib.util
import unittest
from copy import deepcopy
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = REPO_ROOT / "config" / "quality-gates" / "validate_promotion.py"

spec = importlib.util.spec_from_file_location("validate_promotion", VALIDATOR_PATH)
assert spec is not None and spec.loader is not None
validate_promotion = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validate_promotion)

validate = validate_promotion.validate
MANDATORY_GATES = validate_promotion.MANDATORY_GATES
BLOCKING_STATUSES = (
    "NOT_RUN",
    "FAIL",
    "BLOCKED_PERMISSIONS",
    "BLOCKED_CAPACITY",
    "BLOCKED_CONTRACT",
)


def valid_evidence() -> dict[str, Any]:
    gates = [
        {
            "id": gate_id,
            "status": "PASS",
            "command": f"run-{gate_id}",
            "observed_result": "ok",
            "evidence": [f"evidence://{gate_id}"],
        }
        for gate_id in sorted(MANDATORY_GATES)
    ]
    return {
        "version": 1,
        "promotion": "DEV_TO_QA",
        "commit": "abc123",
        "artifact_digest": "sha256:" + "a" * 64,
        "environment_account": "account-x",
        "db_schema_version": "v1",
        "contract_version": "v1",
        "synthetic_dataset": "ds-v1",
        "executed_at": "2026-11-23T00:00:00Z",
        "reviewer": "reviewer-1",
        "manual_approval": {
            "decision": "APPROVED",
            "approved_by": "qa-approver-1",
            "approved_at": "2026-11-23T01:02:03Z",
            "evidence": "approval://qa/SCRUM-49",
        },
        "gates": gates,
    }


class ValidatePromotionTests(unittest.TestCase):
    def test_all_pass_evidence_is_valid(self):
        self.assertEqual(validate(valid_evidence()), [])

    def test_missing_or_invalid_manual_approval_is_rejected(self):
        cases = (
            ("missing object", None, "'manual_approval' must be an object"),
            ("missing decision", {"approved_by": "person", "approved_at": "2026-11-23T01:02:03Z", "evidence": "approval://1"}, "'manual_approval.decision' must be 'APPROVED'"),
            ("rejected decision", {"decision": "REJECTED", "approved_by": "person", "approved_at": "2026-11-23T01:02:03Z", "evidence": "approval://1"}, "'manual_approval.decision' must be 'APPROVED'"),
            ("blank approver", {"decision": "APPROVED", "approved_by": " ", "approved_at": "2026-11-23T01:02:03Z", "evidence": "approval://1"}, "'manual_approval.approved_by' must be a non-empty string"),
            ("blank timestamp", {"decision": "APPROVED", "approved_by": "person", "approved_at": "", "evidence": "approval://1"}, "'manual_approval.approved_at' must be a non-empty string"),
            ("blank evidence", {"decision": "APPROVED", "approved_by": "person", "approved_at": "2026-11-23T01:02:03Z", "evidence": " "}, "'manual_approval.evidence' must be a non-empty string"),
        )
        for name, approval, expected in cases:
            with self.subTest(name=name):
                doc = valid_evidence()
                if approval is None:
                    doc.pop("manual_approval")
                else:
                    doc["manual_approval"] = approval
                self.assertIn(expected, validate(doc))

    def test_invalid_manual_approval_timestamp_is_rejected(self):
        for timestamp in (
            "2026-11-23T01:02:03+00:00",
            "2026-11-23T01:02Z",
            "2026-02-30T01:02:03Z",
            "2026-11-23T01:02:03z",
        ):
            with self.subTest(timestamp=timestamp):
                doc = valid_evidence()
                doc["manual_approval"]["approved_at"] = timestamp
                self.assertIn(
                    "'manual_approval.approved_at' must be an ISO 8601 UTC timestamp",
                    validate(doc),
                )

    def test_complete_waiver_is_valid(self):
        doc = valid_evidence()
        gate = doc["gates"][0]
        gate["status"] = "WAIVED_WITH_ADR"
        for field in ("command", "observed_result", "evidence"):
            gate.pop(field, None)
        gate["waiver"] = {
            "adr": "adr-123",
            "reason": "capacity",
            "approved_by": "reviewer-1",
            "approved_at": "2026-11-01T00:00:00Z",
        }
        self.assertEqual(validate(doc), [])

    def test_each_blocking_status_is_rejected(self):
        for status in BLOCKING_STATUSES:
            with self.subTest(status=status):
                doc = valid_evidence()
                for gate in doc["gates"]:
                    gate["status"] = status
                    for field in ("command", "observed_result", "evidence"):
                        gate.pop(field, None)
                errors = validate(doc)
                self.assertEqual(len(errors), len(MANDATORY_GATES), (status, errors))
                self.assertTrue(
                    all(f"has blocking status '{status}'" in error for error in errors),
                    errors,
                )

    def test_missing_gate_is_rejected(self):
        doc = valid_evidence()
        doc["gates"] = [gate for gate in doc["gates"] if gate["id"] != "unit"]
        self.assertIn("missing mandatory gates: unit", validate(doc))

    def test_duplicate_gate_is_rejected(self):
        doc = valid_evidence()
        unit = next(gate for gate in doc["gates"] if gate["id"] == "unit")
        doc["gates"].append(deepcopy(unit))
        self.assertIn("mandatory gate 'unit' is duplicated", validate(doc))

    def test_unsupported_status_is_rejected(self):
        doc = valid_evidence()
        doc["gates"][0]["status"] = "PENDING"
        self.assertIn("gates[0].status is not allowed", validate(doc))

    def test_incomplete_pass_evidence_is_rejected(self):
        doc = valid_evidence()
        gate = doc["gates"][0]
        gate["command"] = ""
        gate.pop("observed_result")
        gate["evidence"] = []
        errors = validate(doc)
        self.assertIn("gates[0].command is required for PASS", errors)
        self.assertIn("gates[0].observed_result is required for PASS", errors)
        self.assertIn(
            "gates[0].evidence must contain at least one evidence reference", errors
        )

    def test_incomplete_waiver_is_rejected(self):
        doc = valid_evidence()
        gate = doc["gates"][0]
        gate["status"] = "WAIVED_WITH_ADR"
        gate["waiver"] = {"adr": "adr-123"}
        errors = validate(doc)
        for field in ("reason", "approved_by", "approved_at"):
            self.assertIn(f"gates[0].waiver.{field} is required", errors)

    def test_invalid_digest_is_rejected(self):
        for bad_digest in ("not-a-digest", "sha256:" + "a" * 63):
            with self.subTest(digest=bad_digest):
                doc = valid_evidence()
                doc["artifact_digest"] = bad_digest
                self.assertIn(
                    "'artifact_digest' must be a lowercase sha256 digest",
                    validate(doc),
                )


if __name__ == "__main__":
    unittest.main()
