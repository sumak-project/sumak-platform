#!/usr/bin/env python3
"""Fail-closed static boundary checks for DEV private AWS API connectivity."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE = REPO_ROOT / "infra/modules/private-aws-api-connectivity"
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


def sources(directory: Path) -> str:
    files = sorted(directory.glob("*.tf"))
    if not files:
        raise AssertionError(f"Expected Terraform files in {directory}")
    return "\n".join(path.read_text(encoding="utf-8") for path in files)


class DevPrivateAwsApiConnectivityBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = sources(MODULE)
        cls.root = sources(ROOT)

    def test_exact_required_interface_services_have_private_dns_and_supplied_subnets(self):
        interfaces = blocks(self.module, r'resource\s+"aws_vpc_endpoint"')
        interface = next(block for block in interfaces if '"Interface"' in block)
        self.assertRegex(
            interface,
            r'toset\(\["ec2",\s*"ecr\.api",\s*"ecr\.dkr"\]\)',
        )
        self.assertEqual(
            re.findall(r'"(ec2|ecr\.api|ecr\.dkr)"', interface),
            ["ec2", "ecr.api", "ecr.dkr"],
        )
        self.assertRegex(interface, r"private_dns_enabled\s*=\s*true")
        self.assertRegex(interface, r"subnet_ids\s*=\s*var\.subnet_ids")
        self.assertRegex(interface, r'vpc_endpoint_type\s*=\s*"Interface"')

    def test_exactly_one_s3_gateway_endpoint_uses_supplied_route_tables(self):
        endpoints = blocks(self.module, r'resource\s+"aws_vpc_endpoint"')
        gateway = [block for block in endpoints if '"Gateway"' in block]
        self.assertEqual(len(gateway), 1)
        self.assertRegex(gateway[0], r'vpc_endpoint_type\s*=\s*"Gateway"')
        self.assertRegex(gateway[0], r'service_name\s*=.*\.s3"')
        self.assertRegex(gateway[0], r"route_table_ids\s*=\s*var\.route_table_ids")

    def test_endpoint_security_group_allows_only_vpc_scoped_https_ingress(self):
        groups = blocks(self.module, r'resource\s+"aws_security_group"')
        self.assertEqual(len(groups), 1)
        ingress = re.search(r"(?s)ingress\s*\{(.*?)\}", groups[0])
        self.assertIsNotNone(ingress)
        assert ingress is not None
        rule = ingress.group(1)
        self.assertRegex(rule, r"from_port\s*=\s*443")
        self.assertRegex(rule, r"to_port\s*=\s*443")
        self.assertRegex(rule, r'protocol\s*=\s*"tcp"')
        self.assertRegex(rule, r"cidr_blocks\s*=\s*\[var\.vpc_cidr_block\]")
        self.assertEqual(len(re.findall(r"\bingress\s*\{", groups[0])), 1)
        self.assertNotRegex(groups[0], r"(?s)egress\s*\{")

    def test_dev_root_wires_existing_private_network_and_node_group_dependency(self):
        modules = blocks(self.root, r'module')
        connectivity = next(
            block for block in modules if 'module "private_aws_api_connectivity"' in block
        )
        node_group = next(
            block for block in modules if 'module "managed_node_group"' in block
        )
        self.assertIn("../../../../../modules/private-aws-api-connectivity", connectivity)
        self.assertRegex(connectivity, r"vpc_id\s*=\s*data\.aws_vpc\.this\.id")
        self.assertRegex(connectivity, r"vpc_cidr_block\s*=\s*data\.aws_vpc\.this\.cidr_block")
        self.assertRegex(connectivity, r"subnet_ids\s*=\s*var\.private_subnet_ids")
        self.assertRegex(
            connectivity,
            r"route_table_ids\s*=\s*distinct\(\[for route_table in data\.aws_route_table\.private : route_table\.id\]\)",
        )
        self.assertRegex(
            node_group,
            r"depends_on\s*=\s*\[module\.private_aws_api_connectivity\]",
        )
        self.assertNotRegex(self.root, r"aws_(nat_gateway|internet_gateway)")


if __name__ == "__main__":
    unittest.main()
