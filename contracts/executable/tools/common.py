#!/usr/bin/env python3
"""Deterministic contract catalog generation and compatibility validation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = PACKAGE_ROOT.parents[1]
MATRIX_PATH = REPOSITORY_ROOT / "contracts/catalog/api-migration/api-migration-matrix.json"
POLICY_PATH = PACKAGE_ROOT / "catalogo/package-policy.json"
BASELINE_PATH = PACKAGE_ROOT / "catalogo/schemas-baseline.json"
GENERATED_PATH = PACKAGE_ROOT / "generated/contract-catalog.json"

FIELDS = {
    "SOURCE_METHOD_PATH", "SOURCE_ROLE", "BUSINESS_INTENT", "SOURCE_RF_ID",
    "MVP_SCOPE", "NEW_GRAPHQL_OPERATION_OR_GRPC_RPC_OR_EVENT", "OWNER",
    "INPUT_DTO_FIELDS", "OUTPUT_DTO_FIELDS", "AUTH_ABAC", "IDEMPOTENCY_KEY",
    "ERRORS", "TIMEOUT", "RETRY", "VERSION", "TEST_CASE",
}
STATUSES = {"EVIDENCED", "CANDIDATE", "PENDING"}
PROTOCOLS = {
    "clients": "GRAPHQL",
    "internalSync": "GRPC",
    "factsReplay": "KAFKA",
    "work": "RABBITMQ",
    "notifications": "WSS",
    "http": "AUTHORIZED_WEBHOOKS_AND_TECHNICAL_ONLY",
}


class ContractPackageError(ValueError):
    """Fail-closed contract package error."""


def load_json(path: Path) -> dict[str, Any]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ContractPackageError(f"cannot read valid JSON from {path}: {error}") from error
    if not isinstance(document, dict):
        raise ContractPackageError(f"{path} must contain a JSON object")
    return document


def validate_policy(policy: dict[str, Any]) -> None:
    if (
        policy.get("schemaVersion") != 1
        or policy.get("baseline") != "v1"
        or policy.get("approval") != "APPROVED_POLICY_WITH_PENDING_OPERATIONS"
        or policy.get("protocols") != PROTOCOLS
        or policy.get("compatibility", {}).get("supportedVersions") != ["N", "N-1"]
        or policy.get("compatibility", {}).get("baselineRefresh") != "MANUAL_REVIEW_ONLY"
        or policy.get("pendingPolicy", {}).get("generateExecutableContract") is not False
        or policy.get("pendingPolicy", {}).get("result") != "PENDING"
    ):
        raise ContractPackageError("approved v1 policy is invalid")


def validate_matrix(matrix: dict[str, Any]) -> None:
    rows = matrix.get("rows")
    if not isinstance(rows, list) or len(rows) != 162 or matrix.get("rowCount") != 162:
        raise ContractPackageError("migration matrix must contain exactly 162 rows")
    if set(matrix.get("columns", [])) != FIELDS:
        raise ContractPackageError("migration matrix must contain the required 16 fields")
    seen: set[str] = set()
    errors: list[str] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict) or set(row) != FIELDS:
            errors.append(f"rows[{index}] has an invalid field set")
            continue
        for field, cell in row.items():
            if not isinstance(cell, dict) or cell.get("status") not in STATUSES:
                errors.append(f"rows[{index}].{field} has invalid evidence")
                continue
            for required in ("value", "source", "status", "note"):
                if not isinstance(cell.get(required), str) or not cell[required].strip():
                    errors.append(f"rows[{index}].{field}.{required} is required")
        source = row["SOURCE_METHOD_PATH"].get("value")
        if source in seen:
            errors.append(f"duplicate migration source {source}")
        seen.add(source)
    if errors:
        raise ContractPackageError("\n".join(errors))


def _executable(row: dict[str, Any]) -> bool:
    required = (
        "NEW_GRAPHQL_OPERATION_OR_GRPC_RPC_OR_EVENT", "OWNER",
        "INPUT_DTO_FIELDS", "OUTPUT_DTO_FIELDS", "AUTH_ABAC", "ERRORS",
        "VERSION", "TEST_CASE",
    )
    return all(
        row[field]["status"] == "EVIDENCED" and row[field]["value"] != "PENDING"
        for field in required
    )


def build_catalog(matrix: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    validate_matrix(matrix)
    validate_policy(policy)
    entries = []
    for row in matrix["rows"]:
        executable = _executable(row)
        entries.append({
            "sourceMethodPath": row["SOURCE_METHOD_PATH"]["value"],
            "owner": row["OWNER"]["value"],
            "ownerStatus": row["OWNER"]["status"],
            "target": row["NEW_GRAPHQL_OPERATION_OR_GRPC_RPC_OR_EVENT"]["value"],
            "targetStatus": row["NEW_GRAPHQL_OPERATION_OR_GRPC_RPC_OR_EVENT"]["status"],
            "version": row["VERSION"]["value"],
            "versionStatus": row["VERSION"]["status"],
            "executable": executable,
            "generationResult": "GENERATED" if executable else "PENDING",
        })
    generated = sum(entry["executable"] for entry in entries)
    document = {
        "schemaVersion": 1,
        "baseline": "v1",
        "matrixSha256": matrix["contentSha256"],
        "policyApproval": policy["approval"],
        "rowCount": len(entries),
        "generatedCount": generated,
        "pendingCount": len(entries) - generated,
        "status": "GENERATED" if generated == len(entries) else "PENDING",
        "entries": entries,
    }
    payload = json.dumps(document, sort_keys=True, separators=(",", ":")).encode()
    document["contentSha256"] = hashlib.sha256(payload).hexdigest()
    return document


def catalog_bytes(document: dict[str, Any]) -> bytes:
    metadata = {key: value for key, value in document.items() if key != "entries"}
    lines = [json.dumps(metadata, separators=(",", ":"))[:-1] + ',"entries":[']
    entries = document["entries"]
    lines.extend(
        json.dumps(entry, separators=(",", ":"))
        + ("," if index < len(entries) - 1 else "")
        for index, entry in enumerate(entries)
    )
    lines.append("]}")
    return ("\n".join(lines) + "\n").encode()


def generate(check: bool = False) -> dict[str, Any]:
    document = build_catalog(load_json(MATRIX_PATH), load_json(POLICY_PATH))
    expected = catalog_bytes(document)
    if check:
        try:
            actual = GENERATED_PATH.read_bytes()
        except OSError as error:
            raise ContractPackageError(f"generated catalog is missing: {error}") from error
        if actual != expected:
            raise ContractPackageError("generated contract catalog is stale")
    else:
        GENERATED_PATH.parent.mkdir(parents=True, exist_ok=True)
        GENERATED_PATH.write_bytes(expected)
    return document


def check_compatibility() -> dict[str, Any]:
    matrix = load_json(MATRIX_PATH)
    baseline = load_json(BASELINE_PATH)
    catalog = generate(check=True)
    if baseline.get("approvedMatrixSha256") != matrix.get("contentSha256"):
        raise ContractPackageError("matrix digest changed; explicit review is required")
    if not isinstance(baseline.get("contracts"), dict):
        raise ContractPackageError("baseline contracts must be an object")
    generated = {
        entry["target"]: entry["version"]
        for entry in catalog["entries"] if entry["executable"]
    }
    removed = sorted(set(baseline["contracts"]) - set(generated))
    changed = sorted(
        name for name, version in baseline["contracts"].items()
        if generated.get(name) not in (None, version)
    )
    if removed or changed:
        raise ContractPackageError(
            f"breaking compatibility change: removed={removed}, changed={changed}"
        )
    return {
        "status": "PENDING" if catalog["pendingCount"] else "PASS",
        "generated": len(generated),
        "pending": catalog["pendingCount"],
    }
