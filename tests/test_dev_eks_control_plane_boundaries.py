#!/usr/bin/env python3
"""Fail-closed static boundary checks for the EKS control plane."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE = REPO_ROOT / "infra/modules/eks-control-plane"
ROOT = REPO_ROOT / "infra/accounts/sumak-dev/us-east-1/dev/eks"


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


def terraform_sources(directory: Path) -> str:
    files = sorted(directory.glob("*.tf"))
    if not files:
        raise AssertionError(f"Expected Terraform files in {directory}")
    return "\n".join(path.read_text(encoding="utf-8") for path in files)


class DevEksControlPlaneBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = terraform_sources(MODULE)
        cls.root = terraform_sources(ROOT)

    def test_module_creates_exactly_one_cluster_with_preprovisioned_role(self):
        clusters = blocks(self.module, r'resource\s+"aws_eks_cluster"')
        self.assertEqual(len(clusters), 1)
        self.assertRegex(self.module, r'(?m)^\s*variable\s+"cluster_role_arn"')
        self.assertRegex(
            clusters[0], r"(?s)role_arn\s*=\s*var\.cluster_role_arn"
        )
        self.assertRegex(self.module, r'(?m)^\s*output\s+"cluster_name"')
        self.assertRegex(self.module, r"(?s)output\s+\"cluster_name\"\s*\{[^}]*value\s*=\s*aws_eks_cluster\.")

    def test_module_requires_exactly_three_private_subnets_and_availability_zones(self):
        self.assertRegex(self.module, r'(?m)^\s*variable\s+"private_subnet_ids"')
        self.assertRegex(self.module, r'(?m)^\s*variable\s+"availability_zones"')
        self.assertRegex(
            self.module,
            r"(?s)validation\s*\{[^}]*length\(var\.private_subnet_ids\)\s*==\s*3",
        )
        self.assertRegex(
            self.module,
            r"(?s)validation\s*\{[^}]*length\(var\.availability_zones\)\s*==\s*3",
        )
        cluster = blocks(self.module, r'resource\s+"aws_eks_cluster"')[0]
        self.assertRegex(
            cluster,
            r"(?s)vpc_config\s*\{[^}]*subnet_ids\s*=\s*var\.private_subnet_ids",
        )
        self.assertRegex(self.module, r'(?m)^\s*variable\s+"cluster_version"')
        self.assertRegex(self.module, r"(?s)validation\s*\{[^}]*var\.cluster_version")

    def test_endpoint_access_and_all_control_plane_logs_are_explicitly_enabled(self):
        cluster = blocks(self.module, r'resource\s+"aws_eks_cluster"')[0]
        vpc_config = re.search(r"(?s)vpc_config\s*\{(.*?)\}", cluster)
        self.assertIsNotNone(vpc_config)
        assert vpc_config is not None
        self.assertRegex(vpc_config.group(1), r"endpoint_private_access\s*=\s*true")
        self.assertRegex(vpc_config.group(1), r"endpoint_public_access\s*=\s*false")
        logging = re.search(r"(?s)enabled_cluster_log_types\s*=\s*\[(.*?)\]", cluster)
        self.assertIsNotNone(logging)
        assert logging is not None
        for log_type in (
            "api",
            "audit",
            "authenticator",
            "controllerManager",
            "scheduler",
        ):
            self.assertIn(f'"{log_type}"', logging.group(1))

    def test_dev_root_connects_control_plane_and_existing_three_node_group(self):
        modules = blocks(self.root, r'module')
        control_plane = next(
            block for block in modules if 'module "control_plane"' in block
        )
        node_group = next(
            block for block in modules if 'module "managed_node_group"' in block
        )
        self.assertIn("../../../../../modules/eks-control-plane", control_plane)
        self.assertIn("../../../../../modules/eks-managed-node-group", node_group)
        self.assertRegex(
            control_plane, r"(?m)^\s*private_subnet_ids\s*=\s*var\.private_subnet_ids"
        )
        self.assertRegex(
            control_plane, r"(?m)^\s*availability_zones\s*=\s*var\.availability_zones"
        )
        self.assertRegex(
            node_group,
            r"(?m)^\s*cluster_name\s*=\s*module\.control_plane\.cluster_name",
        )

    def test_module_has_tags_and_does_not_own_shared_infrastructure_or_iam(self):
        cluster = blocks(self.module, r'resource\s+"aws_eks_cluster"')[0]
        self.assertRegex(cluster, r"(?m)^\s*tags\s*=\s*var\.\w+")
        for forbidden in (
            "aws_iam_",
            "aws_kms_",
            "aws_vpc",
            "aws_subnet",
            "aws_security_group",
            "assume_role",
        ):
            self.assertNotIn(forbidden, self.module)
        self.assertNotRegex(self.root, r"(?i)\bqa\b|\bprod\b")


if __name__ == "__main__":
    unittest.main()
