#!/usr/bin/env python3
"""Validate fail-closed evidence for a DEV-to-QA promotion."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


POLICY_PATH = Path(__file__).with_name("gate-policy.json")
EXPECTED_MANDATORY_GATES = {
    "unit",
    "architecture",
    "integration",
    "contract",
    "security",
    "load_stress",
}
EXPECTED_BLOCKING_STATUSES = {
    "NOT_RUN",
    "FAIL",
    "PENDING",
    "SKIPPED",
    "CANCELLED",
    "BLOCKED_PERMISSIONS",
    "BLOCKED_CAPACITY",
    "BLOCKED_CONTRACT",
    "WAIVED_WITH_ADR",
}
EXPECTED_PASS_EVIDENCE_FIELDS = {"command", "observed_result", "evidence"}

SHA256_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
GIT_COMMIT_SHA = re.compile(r"^[0-9a-f]{40}$")
ISO_8601_UTC = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _require_text(document: dict[str, Any], field: str, errors: list[str]) -> None:
    if not _non_empty_string(document.get(field)):
        errors.append(f"'{field}' must be a non-empty string")


def _is_iso_8601_utc(value: str) -> bool:
    if not ISO_8601_UTC.fullmatch(value):
        return False
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return False
    return True


def _load_policy() -> Any:
    try:
        return json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def validate_policy(policy: Any) -> list[str]:
    """Validate the immutable six-gate policy used by PR and promotion checks."""
    if not isinstance(policy, dict):
        return ["gate policy must be a JSON object"]

    errors: list[str] = []
    if policy.get("schema_version") != 1:
        errors.append("'schema_version' must be 1")
    if policy.get("promotion") != "DEV_TO_QA":
        errors.append("'promotion' must be 'DEV_TO_QA'")
    if policy.get("pr_target") != "dev":
        errors.append("'pr_target' must be 'dev'")
    if policy.get("required_status") != "PASS":
        errors.append("'required_status' must be 'PASS'")

    gates = policy.get("mandatory_gates")
    if not isinstance(gates, list) or len(gates) != len(set(gates)):
        errors.append("'mandatory_gates' must be an array of unique identifiers")
    elif set(gates) != EXPECTED_MANDATORY_GATES:
        errors.append("'mandatory_gates' must contain the canonical six gates")

    blocking_statuses = policy.get("blocking_statuses")
    if (
        not isinstance(blocking_statuses, list)
        or len(blocking_statuses) != len(set(blocking_statuses))
    ):
        errors.append("'blocking_statuses' must be an array of unique statuses")
    elif set(blocking_statuses) != EXPECTED_BLOCKING_STATUSES:
        errors.append("'blocking_statuses' must contain every fail-closed status")

    evidence_fields = policy.get("pass_evidence_fields")
    if (
        not isinstance(evidence_fields, list)
        or set(evidence_fields) != EXPECTED_PASS_EVIDENCE_FIELDS
    ):
        errors.append(
            "'pass_evidence_fields' must require command, observed_result, and evidence"
        )
    return errors


GATE_POLICY = _load_policy()
MANDATORY_GATES = frozenset(
    GATE_POLICY.get("mandatory_gates", []) if isinstance(GATE_POLICY, dict) else []
)
BLOCKING_STATUSES = frozenset(
    GATE_POLICY.get("blocking_statuses", []) if isinstance(GATE_POLICY, dict) else []
)
ALLOWED_STATUSES = BLOCKING_STATUSES | {"PASS"}
PASS_EVIDENCE_FIELDS = frozenset(
    GATE_POLICY.get("pass_evidence_fields", [])
    if isinstance(GATE_POLICY, dict)
    else []
)


def validate(document: Any) -> list[str]:
    """Return every validation error; an empty list means promotion is allowed."""
    if not isinstance(document, dict):
        return ["evidence must be a JSON object"]

    errors = [f"invalid gate policy: {error}" for error in validate_policy(GATE_POLICY)]
    if document.get("version") != 1:
        errors.append("'version' must be 1")
    if document.get("promotion") != "DEV_TO_QA":
        errors.append("'promotion' must be 'DEV_TO_QA'")

    for field in (
        "commit",
        "artifact_digest",
        "environment_account",
        "db_schema_version",
        "contract_version",
        "synthetic_dataset",
        "executed_at",
        "reviewer",
    ):
        _require_text(document, field, errors)

    digest = document.get("artifact_digest")
    if _non_empty_string(digest) and not SHA256_DIGEST.fullmatch(digest):
        errors.append("'artifact_digest' must be a lowercase sha256 digest")

    commit = document.get("commit")
    if _non_empty_string(commit) and not GIT_COMMIT_SHA.fullmatch(commit):
        errors.append("'commit' must be a full lowercase 40-character Git SHA")

    executed_at = document.get("executed_at")
    if _non_empty_string(executed_at) and not _is_iso_8601_utc(executed_at):
        errors.append("'executed_at' must be an ISO 8601 UTC timestamp")

    approval = document.get("manual_approval")
    if not isinstance(approval, dict):
        errors.append("'manual_approval' must be an object")
    else:
        for field in ("approved_by", "approved_at", "evidence"):
            if not _non_empty_string(approval.get(field)):
                errors.append(f"'manual_approval.{field}' must be a non-empty string")
        if approval.get("decision") != "APPROVED":
            errors.append("'manual_approval.decision' must be 'APPROVED'")
        approved_at = approval.get("approved_at")
        if _non_empty_string(approved_at) and not _is_iso_8601_utc(approved_at):
            errors.append(
                "'manual_approval.approved_at' must be an ISO 8601 UTC timestamp"
            )

    gates = document.get("gates")
    if not isinstance(gates, list):
        errors.append("'gates' must be an array")
        return errors

    seen: set[str] = set()
    for index, gate in enumerate(gates):
        prefix = f"gates[{index}]"
        if not isinstance(gate, dict):
            errors.append(f"{prefix} must be an object")
            continue

        gate_id = gate.get("id")
        if gate_id not in MANDATORY_GATES:
            errors.append(f"{prefix}.id is not a mandatory gate")
        elif gate_id in seen:
            errors.append(f"mandatory gate '{gate_id}' is duplicated")
        else:
            seen.add(gate_id)

        status = gate.get("status")
        if status not in ALLOWED_STATUSES:
            errors.append(f"{prefix}.status is not allowed")
            continue

        if status == "PASS":
            for field in sorted(PASS_EVIDENCE_FIELDS):
                value = gate.get(field)
                if field == "evidence":
                    if not isinstance(value, list) or not value or not all(
                        _non_empty_string(item) for item in value
                    ):
                        errors.append(
                            f"{prefix}.evidence must contain at least one evidence reference"
                        )
                elif not _non_empty_string(value):
                    errors.append(f"{prefix}.{field} is required for PASS")
        elif status == "WAIVED_WITH_ADR":
            waiver = gate.get("waiver")
            if not isinstance(waiver, dict):
                errors.append(f"{prefix}.waiver is required for WAIVED_WITH_ADR")
            else:
                for field in ("adr", "reason", "approved_by", "approved_at"):
                    if not _non_empty_string(waiver.get(field)):
                        errors.append(f"{prefix}.waiver.{field} is required")
            errors.append(
                f"mandatory gate '{gate_id}' has blocking status '{status}'"
            )
        else:
            errors.append(
                f"mandatory gate '{gate_id}' has blocking status '{status}'"
            )

    missing = MANDATORY_GATES - seen
    if missing:
        errors.append(f"missing mandatory gates: {', '.join(sorted(missing))}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Block DEV-to-QA promotion unless mandatory gates pass and manual approval is recorded."
    )
    parser.add_argument(
        "evidence", nargs="?", type=Path, help="path to promotion evidence JSON"
    )
    parser.add_argument(
        "--policy-only",
        action="store_true",
        help="validate and report the repository six-gate policy",
    )
    args = parser.parse_args()

    policy_errors = validate_policy(GATE_POLICY)
    if policy_errors:
        print("Gate policy blocked:", file=sys.stderr)
        for error in policy_errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    if args.policy_only:
        print(
            "Gate policy valid: "
            + ", ".join(GATE_POLICY["mandatory_gates"])
            + "; required status: PASS; target: dev."
        )
        return 0
    if args.evidence is None:
        parser.error("evidence is required unless --policy-only is used")

    try:
        document = json.loads(args.evidence.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"Promotion blocked: cannot read valid JSON evidence: {error}", file=sys.stderr)
        return 2

    errors = validate(document)
    if errors:
        print("Promotion blocked:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("Promotion gate passed: mandatory gates and manual approval are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
