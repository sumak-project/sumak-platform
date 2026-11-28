#!/usr/bin/env python3
"""Static policy checks for the Gradle formatting and verification gates."""

from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/pr-validation.yml"


class GradleQualityGateTests(unittest.TestCase):
    def test_shared_java_conventions_apply_spotless_and_bind_formatting_to_check(self):
        conventions = (
            ROOT / "build-logic/src/main/kotlin/sumak.java-conventions.gradle.kts"
        ).read_text(encoding="utf-8")

        self.assertRegex(
            conventions,
            r'(?m)^\s*id\(["\']com\.diffplug\.spotless["\']\)',
            "Shared Java conventions must apply Spotless to modules",
        )
        self.assertRegex(
            conventions,
            r"(?s)spotless\s*\{.*?java\s*\{.*?googleJavaFormat",
            "Spotless must configure Java formatting",
        )
        self.assertRegex(
            conventions,
            r'ratchetFrom\(["\']origin/dev["\']\)',
            "Spotless must limit formatting checks to changes since origin/dev",
        )

    def test_pull_request_checkout_fetches_history_for_spotless_baseline(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")

        self.assertRegex(
            workflow,
            r"(?s)actions/checkout@.*?fetch-depth:\s*0\b",
            "The PR checkout must fetch history for the origin/dev formatting baseline",
        )
    def test_root_check_aggregates_each_subproject_check(self):
        root_build = (ROOT / "build.gradle.kts").read_text(encoding="utf-8")

        self.assertRegex(
            root_build,
            r"(?s)subprojects\s*\{.*?rootProject\.tasks\.named\(['\"]check['\"]\)"
            r".*?dependsOn\s*\(\s*tasks\.named\(['\"]check['\"]\)\s*\)",
            "Root check must depend on every subproject check",
        )


if __name__ == "__main__":
    unittest.main()
