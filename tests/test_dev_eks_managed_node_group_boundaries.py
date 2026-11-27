#!/usr/bin/env python3
"""Fail-closed static boundary checks for the reusable EKS node group and DEV root."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE = REPO_ROOT / "infra/modules/eks-managed-node-group"
ROOT = REPO_ROOT / "infra/accounts/sumak-dev/us-east-1/dev/eks"
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


def nested_blocks(source: str, name: str) -> list[str]:
    marker = re.compile(rf"\b{re.escape(name)}\s*\{{")
    result = []
    for match in marker.finditer(source):
        depth = 1
        for index in range(match.end(), len(source)):
            depth += (source[index] == "{") - (source[index] == "}")
            if depth == 0:
                result.append(source[match.start():index + 1])
                break
        else:
            raise AssertionError(f"Unclosed {name} block at offset {match.start()}")
    return result


class DevEksManagedNodeGroupBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = "\n".join(
            path.read_text(encoding="utf-8") for path in sorted(MODULE.glob("*.tf"))
        )
        cls.root = "\n".join(
            path.read_text(encoding="utf-8") for path in sorted(ROOT.glob("*.tf"))
        )

    def test_dev_root_is_account_scoped_and_uses_locked_same_account_s3_backend(self):
        self.assertTrue(ROOT.is_dir(), "DEV EKS root must exist")
        self.assertTrue(list(ROOT.glob("*.tf")), "DEV EKS root must contain Terraform")
        self.assertIn(f'allowed_account_ids = ["{ACCOUNT_ID}"]', self.root)
        self.assertRegex(self.root, r'(?m)^\s*Environment\s*=\s*"dev"')
        backend = re.search(r'(?s)backend\s+"s3"\s*\{(.*?)\}', self.root)
        self.assertIsNotNone(backend, "Root must configure an S3 backend")
        assert backend is not None
        self.assertIn(ACCOUNT_ID, backend.group(1))
        self.assertRegex(backend.group(1), r"use_lockfile\s*=\s*true")

    def test_dev_root_consumes_external_cluster_and_three_private_subnet_inputs(self):
        self.assertRegex(self.module, r'(?m)^\s*variable\s+"cluster_name"')
        self.assertRegex(self.module, r'(?m)^\s*variable\s+"subnet_ids"')
        self.assertRegex(self.module, r'(?m)^\s*variable\s+"availability_zones"')
        modules = blocks(self.root, r'module')
        self.assertEqual(len(modules), 1)
        self.assertIn('module "managed_node_group"', modules[0])
        self.assertIn("../../../../../modules/eks-managed-node-group", modules[0])
        self.assertRegex(modules[0], r"(?m)^\s*cluster_name\s*=\s*var\.cluster_name")
        self.assertRegex(modules[0], r"(?m)^\s*subnet_ids\s*=\s*var\.private_subnet_ids")
        self.assertRegex(modules[0], r"(?m)^\s*availability_zones\s*=\s*var\.availability_zones")

    def test_node_group_is_three_fixed_on_demand_t3_large_nodes_in_private_azs(self):
        groups = blocks(self.module, r'resource\s+"aws_eks_node_group"')
        self.assertEqual(len(groups), 1)
        group = groups[0]
        for expression in (
            r'instance_types\s*=\s*\["t3\.large"\]',
            r'capacity_type\s*=\s*"ON_DEMAND"',
            r'min_size\s*=\s*3',
            r'desired_size\s*=\s*3',
            r'max_size\s*=\s*3',
            r'subnet_ids\s*=\s*var\.subnet_ids',
        ):
            self.assertRegex(group, expression)
        self.assertRegex(self.module, r'(?m)^\s*variable\s+"availability_zones"')
        self.assertRegex(self.module, r"(?s)validation\s*\{[^}]*length\(var\.availability_zones\)\s*==\s*3")
        self.assertRegex(self.module, r"(?s)validation\s*\{[^}]*length\(var\.subnet_ids\)\s*==\s*3")
        self.assertRegex(self.root, r'(?m)^\s*variable\s+"private_subnet_ids"')
        self.assertRegex(self.root, r'(?m)^\s*variable\s+"cluster_name"')
        self.assertRegex(self.root, r'(?m)^\s*variable\s+"availability_zones"')
        self.assertRegex(self.module, r'(?m)^\s*variable\s+"node_role_arn"')
        self.assertRegex(self.root, r'(?m)^\s*variable\s+"node_role_arn"')

    def test_ebs_is_bounded_to_100_gb_gp2_and_forbidden_capacity_modes_are_absent(self):
        templates = blocks(self.module, r'resource\s+"aws_launch_template"')
        self.assertEqual(len(templates), 1)
        template = templates[0]
        mappings = nested_blocks(template, "block_device_mappings")
        self.assertEqual(len(mappings), 1)
        mapping = mappings[0]
        self.assertRegex(mapping, r'(?m)^\s*volume_type\s*=\s*"gp2"')
        self.assertRegex(mapping, r"(?m)^\s*encrypted\s*=\s*true")
        self.assertRegex(mapping, r"(?m)^\s*volume_size\s*=\s*(?:var\.\w+|100)")
        self.assertRegex(self.module, r"(?s)validation\s*\{[^}]*var\.\w+\s*<=\s*100")
        group = blocks(self.module, r'resource\s+"aws_eks_node_group"')[0]
        self.assertRegex(group, r"(?s)launch_template\s*\{[^}]*id\s*=\s*aws_launch_template\.")
        self.assertNotRegex(group, r"(?m)^\s*disk_size\s*=")
        for forbidden in ("SPOT", "aws_spot_fleet", "aws_eks_cluster"):
            self.assertNotIn(forbidden, self.module + self.root)

    def test_module_and_root_do_not_create_iam_or_assume_roles_or_other_environments(self):
        for forbidden in ("aws_iam_", "aws_iam", "aws_eks_cluster", "assume_role"):
            self.assertNotIn(forbidden, self.module + self.root)
        self.assertNotRegex(self.root, r"(?m)^\s*provider\s+\"aws\".*alias\s*=")
        self.assertNotRegex(self.root, r"(?i)\bqa\b|\bprod\b")


if __name__ == "__main__":
    unittest.main()
