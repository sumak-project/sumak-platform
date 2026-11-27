#!/usr/bin/env python3
"""Fail-closed static guardrails for the reusable ALB module and DEV root."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE = REPO_ROOT / "infra/modules/alb"
ROOT = REPO_ROOT / "infra/accounts/sumak-dev/us-east-1/dev/alb"
GATEWAY_VALUES = REPO_ROOT / "config/dev/api-gateway-values.yaml"
ACCOUNT_ID = "632080579751"


def blocks(source: str, kind: str) -> list[str]:
    marker = re.compile(rf'{kind}\s+"[^"]+"\s*\{{')
    result = []
    for match in marker.finditer(source):
        depth = 1
        for index in range(match.end(), len(source)):
            depth += (source[index] == "{") - (source[index] == "}")
            if depth == 0:
                result.append(source[match.start():index + 1])
                break
        else:
            raise AssertionError(f"Unclosed {kind} block at offset {match.start()}")
    return result


class DevAlbBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = "\n".join(
            path.read_text(encoding="utf-8") for path in sorted(MODULE.glob("*.tf"))
        )
        cls.root = "\n".join(
            path.read_text(encoding="utf-8") for path in sorted(ROOT.glob("*.tf"))
        )
        cls.gateway_values = GATEWAY_VALUES.read_text(encoding="utf-8")

    def test_root_is_pinned_to_dev_account_and_locked_s3_backend(self):
        self.assertTrue(ROOT.is_dir(), "DEV ALB root must exist")
        self.assertTrue(list(ROOT.glob("*.tf")), "DEV ALB root must contain Terraform")
        self.assertIn(f'allowed_account_ids = ["{ACCOUNT_ID}"]', self.root)
        self.assertRegex(self.root, r'(?m)^\s*Environment\s*=\s*"dev"')
        backend = re.search(r'(?s)backend\s+"s3"\s*\{(.*?)\}', self.root)
        self.assertIsNotNone(backend, "Root must configure an S3 backend")
        assert backend is not None
        self.assertIn(ACCOUNT_ID, backend.group(1))
        self.assertRegex(backend.group(1), r"use_lockfile\s*=\s*true")

    def test_root_consumes_existing_alb_security_group_from_remote_state(self):
        remote = blocks(self.root, r'data\s+"terraform_remote_state"')
        self.assertEqual(len(remote), 1)
        self.assertIn('backend = "s3"', remote[0])
        self.assertIn("network-boundaries/terraform.tfstate", remote[0])
        self.assertIn(ACCOUNT_ID, remote[0])
        modules = blocks(self.root, r'module')
        self.assertEqual(len(modules), 1)
        self.assertIn('module "alb"', modules[0])
        self.assertIn("../../../../../modules/alb", modules[0])
        self.assertIn("data.terraform_remote_state.network_boundaries.outputs.alb_security_group_id", modules[0])

    def test_module_builds_public_multi_subnet_alb_with_parameterized_listener_and_health(self):
        lbs = blocks(self.module, r'resource\s+"aws_lb"')
        self.assertEqual(len(lbs), 1)
        self.assertRegex(lbs[0], r"(?m)^\s*internal\s*=\s*false")
        self.assertRegex(lbs[0], r"(?m)^\s*subnets\s*=\s*var\.")
        self.assertRegex(lbs[0], r"(?m)^\s*security_groups\s*=\s*var\.")
        self.assertRegex(self.module, r"(?m)^\s*variable\s+\"subnet_ids\"")
        self.assertRegex(self.module, r"(?m)^\s*variable\s+\"security_group_id\"")
        listeners = blocks(self.module, r'resource\s+"aws_lb_listener"')
        self.assertGreaterEqual(len(listeners), 1)
        self.assertTrue(any(re.search(r"(?m)^\s*port\s*=\s*var\.", b) for b in listeners))
        targets = blocks(self.module, r'resource\s+"aws_lb_target_group"')
        self.assertEqual(len(targets), 1)
        target = targets[0]
        for setting in ("port", "protocol", "health_check", "deregistration_delay"):
            self.assertRegex(target, rf"(?s)\b{setting}\s*(?:=|\{{)")
        self.assertRegex(self.module, r"(?m)^\s*variable\s+\"idle_timeout\"")
        self.assertRegex(lbs[0], r"(?m)^\s*idle_timeout\s*=\s*var\.idle_timeout")
        self.assertRegex(target, r"(?m)^\s*deregistration_delay\s*=\s*var\.")
        self.assertRegex(target, r"(?s)health_check\s*\{[^}]*var\.")

    def test_alb_health_check_matches_gateway_readiness_path(self):
        self.assertRegex(self.module, r'(?s)variable\s+"health_check_path"\s*\{[^}]*default\s*=\s*"/health/ready"')
        self.assertRegex(self.root, r'(?s)variable\s+"health_check_path"\s*\{[^}]*default\s*=\s*"/health/ready"')
        self.assertRegex(self.gateway_values, r"(?m)^\s+path:\s*/health/ready\s*$")

    def test_forbidden_capabilities_and_unrelated_network_resources_are_absent(self):
        for forbidden in (
            "aws_route53_", "aws_wafv2_", "aws_iam_", "aws_vpc", "aws_subnet",
            "aws_internet_gateway", "aws_nat_gateway", "aws_eip",
            "aws_vpc_peering_connection", "aws_ec2_transit_gateway",
            "aws_vpn_connection", "aws_vpn_gateway",
        ):
            self.assertNotIn(forbidden, self.module + self.root)
        self.assertNotRegex(self.root, r"(?m)^\s*provider\s+\"aws\".*alias\s*=")
        self.assertNotRegex(self.root, r"(?m)^\s*assume_role\s*\{")


if __name__ == "__main__":
    unittest.main()
