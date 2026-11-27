#!/usr/bin/env python3
"""Static security-boundary checks for the network security groups module."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE = REPO_ROOT / "infra" / "modules" / "network-security-groups"


def resource_blocks(source: str, resource_type: str) -> list[str]:
    """Return balanced Terraform resource blocks of the requested type."""
    marker = re.compile(
        rf'resource\s+"{re.escape(resource_type)}"\s+"[^"]+"\s*\{{'
    )
    blocks: list[str] = []
    for match in marker.finditer(source):
        start = match.end()
        depth = 1
        for index in range(start, len(source)):
            if source[index] == "{":
                depth += 1
            elif source[index] == "}":
                depth -= 1
                if depth == 0:
                    blocks.append(source[match.start() : index + 1])
                    break
        else:
            raise AssertionError(f"Unclosed resource block at offset {match.start()}")
    return blocks


class NetworkSecurityGroupBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.main = (MODULE / "main.tf").read_text(encoding="utf-8")
        cls.variables = (MODULE / "variables.tf").read_text(encoding="utf-8")

    def test_public_alb_cannot_expose_ssh_port(self):
        self.assertIn("var.alb_listener_port != 22", self.variables)
        ingress = resource_blocks(
            self.main, "aws_vpc_security_group_ingress_rule"
        )
        self.assertTrue(ingress)
        for block in ingress:
            self.assertNotRegex(block, r"(?m)^\s*from_port\s*=\s*22\s*$")
            self.assertNotRegex(block, r"(?m)^\s*to_port\s*=\s*22\s*$")

    def test_cidr_ingress_is_confined_to_alb_rules(self):
        ingress = resource_blocks(
            self.main, "aws_vpc_security_group_ingress_rule"
        )
        cidr_ingress = [
            block
            for block in ingress
            if re.search(r"(?m)^\s*cidr_ipv[46]\s*=", block)
        ]
        self.assertEqual(len(cidr_ingress), 2)
        for block in cidr_ingress:
            self.assertIn("aws_security_group.alb.id", block)

    def test_east_west_rules_use_security_group_references(self):
        ingress = resource_blocks(
            self.main, "aws_vpc_security_group_ingress_rule"
        )
        egress = resource_blocks(self.main, "aws_vpc_security_group_egress_rule")
        east_west = [
            block
            for block in ingress + egress
            if not re.search(r"(?m)^\s*cidr_ipv[46]\s*=", block)
        ]
        self.assertTrue(east_west)
        for block in east_west:
            self.assertRegex(
                block,
                r"(?m)^\s*referenced_security_group_id\s*=",
                msg=f"East-west rule lacks an SG reference:\n{block}",
            )

    def test_ports_are_parameterized_or_derived(self):
        for resource_type in (
            "aws_vpc_security_group_ingress_rule",
            "aws_vpc_security_group_egress_rule",
        ):
            for block in resource_blocks(self.main, resource_type):
                for field in ("from_port", "to_port"):
                    assignment = re.search(
                        rf"(?m)^\s*{field}\s*=\s*(.+?)\s*$", block
                    )
                    self.assertIsNotNone(assignment, f"{field} is missing:\n{block}")
                    assert assignment is not None
                    self.assertRegex(
                        assignment.group(1),
                        r"^(?:var\.[A-Za-z0-9_]+|each\.value(?:\.[A-Za-z0-9_]+)?)$",
                        msg=f"Unparameterized {field}: {assignment.group(1)}",
                    )

    def test_no_general_peering_resources(self):
        for forbidden in (
            "aws_vpc_peering_connection",
            "aws_vpc_peering_connection_accepter",
            "aws_vpc_peering_connection_options",
            "aws_ec2_transit_gateway",
            "aws_vpn_connection",
        ):
            self.assertEqual(
                resource_blocks(self.main, forbidden),
                [],
                msg=f"Unexpected general connectivity resource: {forbidden}",
            )

    def test_database_ingress_is_only_from_owning_service(self):
        database_ingress = [
            block
            for block in resource_blocks(
                self.main, "aws_vpc_security_group_ingress_rule"
            )
            if (
                'resource "aws_vpc_security_group_ingress_rule" '
                '"database_from_owner"' in block
            )
        ]
        self.assertEqual(len(database_ingress), 1)
        block = database_ingress[0]
        self.assertIn("aws_security_group.database[each.key].id", block)
        self.assertIn("aws_security_group.service[each.key].id", block)
        self.assertIn("each.value.database_port", block)
        self.assertNotRegex(block, r"(?m)^\s*cidr_ipv[46]\s*=")


if __name__ == "__main__":
    unittest.main()
