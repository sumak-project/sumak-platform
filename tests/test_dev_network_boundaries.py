#!/usr/bin/env python3
"""Fail-closed static guardrails for the DEV network-boundaries root."""

from __future__ import annotations

import ipaddress
import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ROOT = REPO_ROOT / "infra/accounts/sumak-dev/us-east-1/dev/network-boundaries"
NETWORK_ROOT = REPO_ROOT / "infra/accounts/sumak-dev/us-east-1/dev/network"
VPC_MODULE = REPO_ROOT / "infra/modules/vpc"
SG_MODULE = REPO_ROOT / "infra/modules/network-security-groups"
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


class DevNetworkBoundariesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = "\n".join(p.read_text(encoding="utf-8") for p in sorted(ROOT.glob("*.tf")))
        cls.network_root = "\n".join(
            p.read_text(encoding="utf-8") for p in sorted(NETWORK_ROOT.glob("*.tf"))
        )
        cls.vpc_module = "\n".join(
            p.read_text(encoding="utf-8") for p in sorted(VPC_MODULE.glob("*.tf"))
        )
        cls.sg_module = "\n".join(
            p.read_text(encoding="utf-8") for p in sorted(SG_MODULE.glob("*.tf"))
        )

    def test_root_materialized_same_account_and_locked_backend(self):
        self.assertTrue(ROOT.is_dir(), "DEV network-boundaries root must exist")
        self.assertTrue(list(ROOT.glob("*.tf")), "Root must contain Terraform configuration")
        self.assertIn(f'allowed_account_ids = ["{ACCOUNT_ID}"]', self.root)
        backend = re.search(r'(?s)backend\s+"s3"\s*\{(.*?)\}', self.root)
        self.assertIsNotNone(backend, "Root must configure an S3 backend")
        assert backend is not None
        self.assertIn(ACCOUNT_ID, backend.group(1))
        self.assertRegex(backend.group(1), r"use_lockfile\s*=\s*true")
        self.assertEqual(len(list(ROOT.glob(".terraform.lock.hcl"))), 1)
        self.assertRegex(self.root, r'(?m)^\s*Environment\s*=\s*"dev"')

    def test_remote_state_and_security_group_module_are_wired(self):
        remote = blocks(self.root, r'data\s+"terraform_remote_state"')
        self.assertEqual(len(remote), 1)
        self.assertIn('backend = "s3"', remote[0])
        self.assertIn("network/terraform.tfstate", remote[0])
        self.assertIn(ACCOUNT_ID, remote[0])
        modules = blocks(self.root, r'module')
        self.assertEqual(len(modules), 1)
        self.assertIn('module "network_security_groups"', modules[0])
        self.assertIn("../../../../../modules/network-security-groups", modules[0])
        self.assertIn("data.terraform_remote_state.network.outputs.vpc_id", modules[0])
        self.assertIn("var.allowed_ingress_ipv4_cidrs", modules[0])
        self.assertIn("var.allowed_ingress_ipv6_cidrs", modules[0])

    def test_shared_vpc_has_public_only_igw_route_and_private_app_data_tiers(self):
        self.assertIn("data.terraform_remote_state.network.outputs.vpc_id", self.root)
        public_routes = blocks(self.vpc_module, r'resource\s+"aws_route"')
        self.assertEqual(len(public_routes), 1)
        self.assertIn("aws_internet_gateway.public_ingress.id", public_routes[0])
        self.assertRegex(public_routes[0], r'if\s+subnet\.tier\s*==\s*"public"')
        tiers = re.search(r"(?s)subnet_tiers\s*=\s*\{(.*?)\n\s{2}\}", self.vpc_module)
        self.assertIsNotNone(tiers)
        assert tiers is not None
        self.assertRegex(tiers.group(1), r"application\s*=\s*\{[^}]*public_ip\s*=\s*false")
        self.assertRegex(tiers.group(1), r"data\s*=\s*\{[^}]*public_ip\s*=\s*false")
        for forbidden in (
            "aws_nat_gateway", "aws_eip", "aws_vpc_peering_connection",
            "aws_ec2_transit_gateway", "aws_vpn_connection", "aws_vpn_gateway",
        ):
            self.assertEqual(blocks(self.vpc_module, rf'resource\s+"{forbidden}"'), [])
            self.assertEqual(blocks(self.root, rf'resource\s+"{forbidden}"'), [])

    def test_physical_az_ids_and_nine_unique_non_overlapping_network_cidrs(self):
        expected_zones = {"use1-az2", "use1-az4", "use1-az6"}
        zones = set(re.findall(r'(?m)^\s*zone_id\s*=\s*"([^"]+)"', self.network_root))
        self.assertEqual(zones, expected_zones)
        self.assertNotRegex(self.root, r'(?m)^\s*(?:public|application|data)_cidr\s*=')
        cidrs = re.findall(
            r'(?m)^\s*(?:public_cidr|application_cidr|data_cidr)\s*=\s*"([^"]+)"',
            self.network_root,
        )
        self.assertEqual(len(cidrs), 9)
        networks = [ipaddress.ip_network(cidr, strict=True) for cidr in cidrs]
        self.assertEqual(len(set(networks)), 9)
        self.assertTrue(all(n.subnet_of(ipaddress.ip_network("10.10.0.0/16")) for n in networks))
        for index, network in enumerate(networks):
            self.assertFalse(
                any(network.overlaps(other) for other in networks[index + 1:]),
                f"Overlapping CIDR: {network}",
            )

    def test_cidr_ingress_is_limited_to_alb(self):
        ingress = blocks(self.sg_module, r'resource\s+"aws_vpc_security_group_ingress_rule"')
        cidr_rules = [rule for rule in ingress if re.search(r"(?m)^\s*cidr_ipv[46]\s*=", rule)]
        self.assertEqual(len(cidr_rules), 2)
        for rule in cidr_rules:
            self.assertIn("aws_security_group.alb.id", rule)

    def test_database_paths_remain_owner_scoped(self):
        database_ingress = blocks(
            self.sg_module, r'resource\s+"aws_vpc_security_group_ingress_rule"'
        )
        owner_rules = [
            rule for rule in database_ingress
            if 'resource "aws_vpc_security_group_ingress_rule" "database_from_owner"' in rule
        ]
        self.assertEqual(len(owner_rules), 1)
        self.assertIn("aws_security_group.database[each.key].id", owner_rules[0])
        self.assertIn("aws_security_group.service[each.key].id", owner_rules[0])
        self.assertIn("each.value.database_port", owner_rules[0])
        self.assertNotRegex(owner_rules[0], r"(?m)^\s*cidr_ipv[46]\s*=")
        database_egress = blocks(
            self.sg_module, r'resource\s+"aws_vpc_security_group_egress_rule"'
        )
        owner_egress = [
            rule for rule in database_egress
            if 'resource "aws_vpc_security_group_egress_rule" "service_to_database"' in rule
        ]
        self.assertEqual(len(owner_egress), 1)
        self.assertIn("aws_security_group.service[each.key].id", owner_egress[0])
        self.assertIn("aws_security_group.database[each.key].id", owner_egress[0])


if __name__ == "__main__":
    unittest.main()
