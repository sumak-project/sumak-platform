#!/usr/bin/env python3
"""Dependency-free guards for narrowly scoped Trivy suppressions."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def resource(source: str, resource_type: str) -> str:
    match = re.search(
        rf'resource\s+"{re.escape(resource_type)}"\s+"[^"]+"\s*\{{', source
    )
    if match is None:
        raise AssertionError(f"Missing {resource_type} resource")
    depth = 1
    for index in range(match.end(), len(source)):
        depth += (source[index] == "{") - (source[index] == "}")
        if depth == 0:
            return source[match.start():index + 1]
    raise AssertionError(f"Unclosed {resource_type} resource")


def assert_narrow_suppression(test: unittest.TestCase, path: str, check: str,
                              phrases: tuple[str, ...]) -> str:
    source = (ROOT / path).read_text(encoding="utf-8")
    lines = source.splitlines()
    indexes = [i for i, line in enumerate(lines) if f"#trivy:ignore:{check}" in line]
    test.assertEqual(len(indexes), 1, f"{check} must have one narrow suppression")
    index = indexes[0]
    test.assertGreater(index, 0)
    rationale = "\n".join(lines[max(0, index - 3):index])
    for phrase in phrases:
        test.assertIn(phrase, rationale.lower())
    return resource(source, {
        "AVD-AWS-0053": "aws_lb",
        "AVD-AWS-0164": "aws_subnet",
        "AVD-AWS-0039": "aws_eks_cluster",
    }[check])


class TrivySuppressionBoundaryTests(unittest.TestCase):
    def test_public_alb_suppression_preserves_public_ingress_configuration(self):
        block = assert_narrow_suppression(
            self, "infra/modules/alb/main.tf", "AVD-AWS-0053",
            ("public ingress",),
        )
        self.assertRegex(block, r"(?m)^\s*internal\s*=\s*false\s*$")

    def test_vpc_suppression_is_limited_to_conditional_public_ingress_tiers(self):
        block = assert_narrow_suppression(
            self, "infra/modules/vpc/main.tf", "AVD-AWS-0164",
            ("public ingress tier",),
        )
        self.assertRegex(
            block, r"(?m)^\s*map_public_ip_on_launch\s*=\s*each\.value\.public_ip\s*$"
        )
        tiers = (ROOT / "infra/modules/vpc/main.tf").read_text(encoding="utf-8")
        self.assertRegex(tiers, r"(?s)application\s*=\s*\{[^}]*public_ip\s*=\s*false")
        self.assertRegex(tiers, r"(?s)data\s*=\s*\{[^}]*public_ip\s*=\s*false")

    def test_eks_suppression_rationale_is_version_and_private_cluster_specific(self):
        block = assert_narrow_suppression(
            self, "infra/modules/eks-control-plane/main.tf", "AVD-AWS-0039",
            ("versions are >=1.28", "default", "envelope encryption", "cluster remains private"),
        )
        self.assertRegex(block, r"(?s)endpoint_private_access\s*=\s*true")
        self.assertRegex(block, r"(?s)endpoint_public_access\s*=\s*false")


if __name__ == "__main__":
    unittest.main()
