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


MANDATORY_GATES = {
    "unit",
    "architecture",
    "integration",
    "contract",
    "security",
    "load_stress",
}

ALLOWED_STATUSES = {
    "NOT_RUN",
    "PASS",
    "FAIL",
    "BLOCKED_PERMISSIONS",
    "BLOCKED_CAPACITY",
    "BLOCKED_CONTRACT",
    "WAIVED_WITH_ADR",
}

SHA256_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
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


def validate(document: Any) -> list[str]:
    """Return every validation error; an empty list means promotion is allowed."""
    if not isinstance(document, dict):
        return ["evidence must be a JSON object"]

    errors: list[str] = []
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
            for field in ("command", "observed_result", "evidence"):
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
    parser.add_argument("evidence", type=Path, help="path to promotion evidence JSON")
    args = parser.parse_args()

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
