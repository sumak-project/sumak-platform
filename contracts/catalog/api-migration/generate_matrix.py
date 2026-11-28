#!/usr/bin/env python3
"""Generate and validate the candidate API migration matrix deterministically."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
ROUTES_PATH = ROOT / "source-routes.tsv"
OVERRIDES_PATH = ROOT / "overrides.json"
JSON_PATH = ROOT / "api-migration-matrix.json"
CSV_PATH = ROOT / "api-migration-matrix.csv"

FIELDS = (
    "SOURCE_METHOD_PATH",
    "SOURCE_ROLE",
    "BUSINESS_INTENT",
    "SOURCE_RF_ID",
    "MVP_SCOPE",
    "NEW_GRAPHQL_OPERATION_OR_GRPC_RPC_OR_EVENT",
    "OWNER",
    "INPUT_DTO_FIELDS",
    "OUTPUT_DTO_FIELDS",
    "AUTH_ABAC",
    "IDEMPOTENCY_KEY",
    "ERRORS",
    "TIMEOUT",
    "RETRY",
    "VERSION",
    "TEST_CASE",
)
ALLOWED_STATUSES = {"EVIDENCED", "CANDIDATE", "PENDING"}
METHOD_PATH = re.compile(
    r"^(GET|POST|PUT|PATCH|DELETE|HEAD) (/v1/(mobile|admin|public|integration)/\S+)$"
)
EXPECTED_SURFACES = {"mobile": 55, "admin": 87, "public": 15, "integration": 5}
ROUTE_PROVENANCE = {
    "source": "Confluence content 6356993, version 2, 2026-11-08",
    "status": "CANDIDATE",
    "note": (
        "Historical v2.5.1 route inventory only. It is not approval of REST as "
        "the current client protocol."
    ),
}
OWNER_PROVENANCE = {
    "source": "Confluence content 6356993 ownership reconciliation table",
    "status": "CANDIDATE",
    "note": "Must be reconciled with current service boundaries before approval.",
}
PENDING_PROVENANCE = {
    "source": (
        "docs/11_Contratos/06_Verificacion_API_v2_5_1_y_alcance_GraphQL.md"
    ),
    "status": "PENDING",
    "note": "Requires row-level validation against current authoritative sources.",
}


class MatrixError(ValueError):
    """Raised when the source or generated matrix violates its contract."""


def _cell(value: str, provenance: dict[str, str]) -> dict[str, str]:
    return {"value": value, **provenance}


def _load_routes() -> list[dict[str, str]]:
    with ROUTES_PATH.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))
    expected_headers = ["SOURCE_METHOD_PATH", "OWNER"]
    if not rows or list(rows[0]) != expected_headers:
        raise MatrixError(f"{ROUTES_PATH} must use headers {expected_headers}")
    return rows


def _load_overrides() -> dict[str, Any]:
    try:
        document = json.loads(OVERRIDES_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise MatrixError(f"cannot read overrides: {error}") from error
    if document.get("version") != 1 or not isinstance(document.get("rows"), dict):
        raise MatrixError("overrides must contain version 1 and an object named rows")
    return document["rows"]


def _validate_sources(
    routes: list[dict[str, str]], overrides: dict[str, Any]
) -> Counter[str]:
    errors: list[str] = []
    keys: set[str] = set()
    surfaces: Counter[str] = Counter()
    for index, route in enumerate(routes, start=2):
        key = route.get("SOURCE_METHOD_PATH", "").strip()
        owner = route.get("OWNER", "").strip()
        match = METHOD_PATH.fullmatch(key)
        if not match:
            errors.append(f"source-routes.tsv:{index}: invalid method/path '{key}'")
            continue
        if key in keys:
            errors.append(f"source-routes.tsv:{index}: duplicate '{key}'")
        keys.add(key)
        surfaces[match.group(3)] += 1
        if not owner:
            errors.append(f"source-routes.tsv:{index}: OWNER is empty")

    if len(routes) != 162:
        errors.append(f"expected 162 source routes, found {len(routes)}")
    if dict(surfaces) != EXPECTED_SURFACES:
        errors.append(
            f"expected surface counts {EXPECTED_SURFACES}, found {dict(surfaces)}"
        )

    unknown_overrides = sorted(set(overrides) - keys)
    if unknown_overrides:
        errors.append(f"overrides contain unknown routes: {unknown_overrides}")

    for key, fields in overrides.items():
        if not isinstance(fields, dict):
            errors.append(f"override '{key}' must be an object")
            continue
        for field, cell in fields.items():
            if field not in FIELDS or field in {"SOURCE_METHOD_PATH", "OWNER"}:
                errors.append(f"override '{key}' has unsupported field '{field}'")
                continue
            if not isinstance(cell, dict):
                errors.append(f"override '{key}.{field}' must be an object")
                continue
            if cell.get("status") not in ALLOWED_STATUSES:
                errors.append(f"override '{key}.{field}' has invalid status")
            for required in ("value", "source", "status", "note"):
                if not isinstance(cell.get(required), str) or not cell[required].strip():
                    errors.append(f"override '{key}.{field}.{required}' is required")

    if errors:
        raise MatrixError("\n".join(errors))
    return surfaces


def _build_matrix(
    routes: list[dict[str, str]], overrides: dict[str, Any]
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for route in routes:
        key = route["SOURCE_METHOD_PATH"].strip()
        row = {
            field: _cell("PENDING", PENDING_PROVENANCE) for field in FIELDS
        }
        row["SOURCE_METHOD_PATH"] = _cell(key, ROUTE_PROVENANCE)
        row["OWNER"] = _cell(route["OWNER"].strip(), OWNER_PROVENANCE)
        for field, cell in overrides.get(key, {}).items():
            row[field] = cell
        rows.append(row)

    document: dict[str, Any] = {
        "schemaVersion": 1,
        "classification": "CANDIDATE_PARTIAL",
        "approval": "PENDING",
        "columns": list(FIELDS),
        "rowCount": len(rows),
        "surfaceCounts": dict(
            sorted(
                Counter(
                    row["SOURCE_METHOD_PATH"]["value"].split("/")[2] for row in rows
                ).items()
            )
        ),
        "sourcePolicy": {
            "currentArchitecture": (
                "GraphQL for clients, gRPC internally, Kafka for facts/replay, "
                "RabbitMQ for work, WSS for notifications, and HTTP only for "
                "authorized webhooks or technical interfaces."
            ),
            "historicalRestInventory": "Candidate input; never executable output.",
            "pendingSemantics": "PENDING is not approval, implementation, or PASS.",
        },
        "rows": rows,
    }
    payload = json.dumps(document, ensure_ascii=False, sort_keys=True).encode()
    document["contentSha256"] = hashlib.sha256(payload).hexdigest()
    return document


def _validate_matrix(document: dict[str, Any]) -> None:
    errors: list[str] = []
    rows = document.get("rows")
    if document.get("columns") != list(FIELDS):
        errors.append("matrix columns do not match the required 16-column contract")
    if document.get("rowCount") != 162 or not isinstance(rows, list) or len(rows) != 162:
        errors.append("matrix must contain exactly 162 rows")
        rows = rows if isinstance(rows, list) else []

    seen: set[str] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict) or set(row) != set(FIELDS):
            errors.append(f"rows[{index}] must contain exactly the required fields")
            continue
        key = row["SOURCE_METHOD_PATH"].get("value")
        if key in seen:
            errors.append(f"rows[{index}] duplicates '{key}'")
        seen.add(key)
        for field in FIELDS:
            cell = row[field]
            if not isinstance(cell, dict):
                errors.append(f"rows[{index}].{field} must be an object")
                continue
            if cell.get("status") not in ALLOWED_STATUSES:
                errors.append(f"rows[{index}].{field}.status is invalid")
            for required in ("value", "source", "status", "note"):
                if not isinstance(cell.get(required), str) or not cell[required].strip():
                    errors.append(f"rows[{index}].{field}.{required} is required")
    if errors:
        raise MatrixError("\n".join(errors))


def _json_bytes(document: dict[str, Any]) -> bytes:
    metadata = {key: value for key, value in document.items() if key != "rows"}
    metadata_json = json.dumps(
        metadata, ensure_ascii=False, sort_keys=False, separators=(",", ":")
    )
    lines = [metadata_json[:-1] + ',"rows":[']
    rows = document["rows"]
    lines.extend(
        json.dumps(row, ensure_ascii=False, separators=(",", ":"))
        + ("," if index < len(rows) - 1 else "")
        for index, row in enumerate(rows)
    )
    lines.append("]}")
    return ("\n".join(lines) + "\n").encode("utf-8")


def _csv_bytes(document: dict[str, Any]) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    headers = [item for field in FIELDS for item in (field, f"{field}_STATUS")]
    writer.writerow(headers)
    for row in document["rows"]:
        writer.writerow(
            item
            for field in FIELDS
            for item in (row[field]["value"], row[field]["status"])
        )
    return output.getvalue().encode("utf-8")


def _check_file(path: Path, expected: bytes) -> bool:
    try:
        actual = path.read_bytes()
    except OSError:
        return False
    return actual == expected


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate or check the 162-row candidate API migration matrix."
    )
    parser.add_argument(
        "--check", action="store_true", help="fail when generated files are stale"
    )
    args = parser.parse_args()
    try:
        routes = _load_routes()
        overrides = _load_overrides()
        surfaces = _validate_sources(routes, overrides)
        document = _build_matrix(routes, overrides)
        _validate_matrix(document)
        outputs = {JSON_PATH: _json_bytes(document), CSV_PATH: _csv_bytes(document)}
        if args.check:
            stale = [str(path.relative_to(ROOT)) for path, data in outputs.items()
                     if not _check_file(path, data)]
            if stale:
                raise MatrixError(f"generated files are stale or missing: {stale}")
        else:
            for path, data in outputs.items():
                path.write_bytes(data)
        print(
            "API migration matrix valid: "
            f"{len(routes)} rows; surfaces={dict(sorted(surfaces.items()))}; "
            "approval=PENDING"
        )
    except MatrixError as error:
        print(f"API migration matrix invalid:\n{error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
