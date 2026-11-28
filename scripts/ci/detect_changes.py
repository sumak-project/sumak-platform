#!/usr/bin/env python3
"""Route reviewed PR changes to the smallest documented CI validation scope."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[2]
ROUTING_CONFIG = REPOSITORY / "config/ci/path-routing.json"
GRADLE_COMPONENT_PREFIXES = ("services/", "platform/")
GRADLE_SHARED_INPUTS = {
    "build.gradle",
    "build.gradle.kts",
    "settings.gradle",
    "settings.gradle.kts",
    "gradle.properties",
}


def changed_paths(base: str, head: str) -> list[str]:
    result = subprocess.run(
        [
            "git",
            "diff",
            "--name-only",
            "--diff-filter=ACMRTD",
            base,
            head,
        ],
        cwd=REPOSITORY,
        check=True,
        capture_output=True,
        text=True,
    )
    return [path for path in result.stdout.splitlines() if path]


def is_gradle_dependency_input(path: str) -> bool:
    name = Path(path).name
    return (
        name in GRADLE_SHARED_INPUTS
        or name.endswith((".gradle", ".gradle.kts"))
        or path.startswith("build-logic/")
        or path.startswith("gradle/wrapper/")
        or path == "gradle/libs.versions.toml"
        or "/gradle/" in path and name.endswith(".versions.toml")
        or name == "gradle.lockfile"
        or "/gradle/dependency-locks/" in f"/{path}"
    )


def gradle_project(path: str) -> str | None:
    parts = Path(path).parts
    if len(parts) < 2 or not path.startswith(GRADLE_COMPONENT_PREFIXES):
        return None
    project_dir = REPOSITORY.joinpath(*parts[:2])
    if not any(
        (project_dir / build_file).is_file()
        for build_file in ("build.gradle", "build.gradle.kts")
    ):
        return None
    return f":{parts[0]}:{parts[1]}"


def validate_consumer(project: str) -> bool:
    parts = project.removeprefix(":").split(":")
    if len(parts) != 2 or parts[0] not in {"services", "platform"}:
        return False
    project_dir = REPOSITORY.joinpath(*parts)
    return any(
        (project_dir / build_file).is_file()
        for build_file in ("build.gradle", "build.gradle.kts")
    )


def route(paths: list[str]) -> dict[str, str]:
    config = json.loads(ROUTING_CONFIG.read_text(encoding="utf-8"))
    source_prefixes = tuple(config["contractSourcePrefixes"])
    consumer_map: dict[str, list[str]] = config["contractConsumers"]

    terraform_changed = any(
        path.endswith(".tf")
        and path.startswith(("infra/accounts/", "infra/modules/"))
        for path in paths
    )
    dependency_inputs_changed = any(is_gradle_dependency_input(path) for path in paths)
    contract_sources = sorted(path for path in paths if path.startswith(source_prefixes))
    projects = {project for path in paths if (project := gradle_project(path))}
    unresolved_contracts: list[str] = []

    for source in contract_sources:
        consumers = consumer_map.get(source)
        if not consumers:
            unresolved_contracts.append(source)
            continue
        invalid_consumers = [consumer for consumer in consumers if not validate_consumer(consumer)]
        if invalid_consumers:
            unresolved_contracts.append(
                f"{source} (invalid mapped consumers: {', '.join(invalid_consumers)})"
            )
            continue
        projects.update(consumers)

    if dependency_inputs_changed:
        gradle_tasks = "check"
    else:
        gradle_tasks = " ".join(f"{project}:check" for project in sorted(projects))

    return {
        "terraform_changed": str(terraform_changed).lower(),
        "gradle_dependency_inputs_changed": str(dependency_inputs_changed).lower(),
        "contract_changed": str(bool(contract_sources)).lower(),
        "gradle_changed": str(bool(gradle_tasks)).lower(),
        "gradle_tasks": gradle_tasks,
        "blocked": str(bool(unresolved_contracts)).lower(),
        "blocked_reason": (
            "BLOCKED: no documented dependent consumers for contract source(s): "
            + ", ".join(unresolved_contracts)
            if unresolved_contracts
            else ""
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args()
    outputs = route(changed_paths(args.base, args.head))

    destination = args.github_output
    if destination:
        with destination.open("a", encoding="utf-8") as output:
            for key, value in outputs.items():
                output.write(f"{key}={value}\n")
    else:
        print(json.dumps(outputs, indent=2, sort_keys=True))

    if outputs["blocked"] == "true":
        print(f"::error::{outputs['blocked_reason']}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
