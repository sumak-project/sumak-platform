#!/usr/bin/env python3
"""Fail closed until official compiler pins and executable schemas are present."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


COMMIT_SHA = re.compile(r"^[0-9a-f]{40}$")
PINNED_VERSION = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")
SCHEMA_SUFFIXES = {".graphql", ".graphqls", ".proto", ".yaml", ".yml"}
EXCLUDED_SCHEMA_PARTS = {"catalog", "catalogo", "generated"}


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _write_evidence(
    path: Path | None,
    *,
    commit: str,
    status: str,
    reasons: list[str],
    tools: list[dict[str, Any]],
    schema_count: int,
) -> None:
    if path is None:
        return
    document = {
        "schemaVersion": 1,
        "sourceCommit": commit,
        "status": status,
        "compilerExecution": "NOT_RUN",
        "command": "scripts/ci/check_official_contract_compilers.py",
        "toolVersions": {
            tool["name"]: tool["version"]
            for tool in tools
            if _text(tool.get("name")) and _text(tool.get("version"))
        },
        "executableSchemaCount": schema_count,
        "reasons": reasons,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _load_manifest(path: Path, errors: list[str]) -> list[dict[str, Any]]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append("official compiler manifest is missing")
        return []
    except (OSError, json.JSONDecodeError) as error:
        errors.append(f"official compiler manifest is invalid: {error}")
        return []

    tools = document.get("tools") if isinstance(document, dict) else None
    if not isinstance(tools, list) or not tools:
        errors.append("official compiler manifest must define a non-empty tools array")
        return []

    validated: list[dict[str, Any]] = []
    for index, tool in enumerate(tools):
        prefix = f"tools[{index}]"
        if not isinstance(tool, dict):
            errors.append(f"{prefix} must be an object")
            continue
        name = tool.get("name")
        version = tool.get("version")
        command = tool.get("command")
        if not _text(name):
            errors.append(f"{prefix}.name must be a non-empty string")
        if not _text(version) or not PINNED_VERSION.fullmatch(version):
            errors.append(f"{prefix}.version must be an exact semantic version")
        if (
            not isinstance(command, list)
            or not command
            or not all(_text(argument) for argument in command)
        ):
            errors.append(f"{prefix}.command must be a non-empty string array")
        if (
            _text(name)
            and _text(version)
            and PINNED_VERSION.fullmatch(version)
            and isinstance(command, list)
            and command
            and all(_text(argument) for argument in command)
        ):
            validated.append(tool)
    return validated


def _schema_inputs(root: Path) -> list[Path]:
    contracts = root / "contracts"
    if not contracts.is_dir():
        return []
    return sorted(
        path
        for path in contracts.rglob("*")
        if path.is_file()
        and path.suffix.lower() in SCHEMA_SUFFIXES
        and not EXCLUDED_SCHEMA_PARTS.intersection(path.relative_to(contracts).parts)
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate official compiler prerequisites without executing compilers "
            "or modifying contract inputs."
        )
    )
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("contracts/executable/validacion/compiler-manifest.json"),
    )
    parser.add_argument("--evidence", type=Path)
    args = parser.parse_args()

    root = args.root.resolve()
    manifest = args.manifest
    if not manifest.is_absolute():
        manifest = root / manifest
    manifest = manifest.resolve()

    errors: list[str] = []
    try:
        manifest.relative_to(root)
    except ValueError:
        errors.append("official compiler manifest must be inside the repository root")

    commit = os.environ.get("GITHUB_SHA", "")
    if not COMMIT_SHA.fullmatch(commit):
        errors.append("GITHUB_SHA must be a full lowercase 40-character Git SHA")

    tools = _load_manifest(manifest, errors) if not errors else []
    schemas = _schema_inputs(root)
    if not schemas:
        errors.append("no executable contract schema inputs are present")

    if errors:
        _write_evidence(
            args.evidence,
            commit=commit,
            status="BLOCKED_CONTRACT",
            reasons=errors,
            tools=tools,
            schema_count=len(schemas),
        )
        print("BLOCKED_CONTRACT: official compiler prerequisites are incomplete")
        for error in errors:
            print(f"- {error}")
        return 1

    _write_evidence(
        args.evidence,
        commit=commit,
        status="PREREQUISITES_VALID",
        reasons=[
            "Pinned compiler prerequisites and executable schema inputs are present.",
            "Compiler execution remains NOT_RUN.",
        ],
        tools=tools,
        schema_count=len(schemas),
    )
    print(
        "PREREQUISITES_VALID: official compiler inputs are pinned; "
        "compiler execution remains NOT_RUN"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
