#!/usr/bin/env python3
"""Static guardrails for the DEV VPC module and account root."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE = REPO_ROOT / "infra/modules/vpc"
ROOT = REPO_ROOT / "infra/accounts/sumak-dev/us-east-1/dev/network"
ACCOUNT_ID = "632080579751"


def blocks(source: str, kind: str) -> list[str]:
    marker = re.compile(rf'{kind}\s+"[^"]+"\s*\{{')
    found = []
    for match in marker.finditer(source):
        depth = 1
        for i in range(match.end(), len(source)):
            depth += (source[i] == "{") - (source[i] == "}")
            if depth == 0:
                found.append(source[match.start():i + 1])
                break
        else:
            raise AssertionError(f"Unclosed {kind} block at {match.start()}")
    return found


def object_entries(source: str) -> list[tuple[str, str]]:
    """Extract simple named HCL object entries, balancing nested braces."""
    entries = []
    for match in re.finditer(r"(?m)^\s*([A-Za-z0-9_-]+)\s*=\s*\{", source):
        depth = 1
        quote = False
        for index in range(match.end(), len(source)):
            char = source[index]
            if char == '"' and (index == 0 or source[index - 1] != "\\"):
                quote = not quote
            if not quote:
                depth += (char == "{") - (char == "}")
            if depth == 0:
                entries.append((match.group(1), source[match.end():index]))
                break
        else:
            raise AssertionError(f"Unclosed object entry {match.group(1)}")
    return entries


class DevVpcBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = "\n".join(p.read_text() for p in sorted(MODULE.glob("*.tf")))
        cls.root = "\n".join(p.read_text() for p in sorted(ROOT.glob("*.tf")))

    def test_account_root_is_dev_only_account_scoped_and_has_lockfile_backend(self):
        self.assertIn(f'allowed_account_ids = ["{ACCOUNT_ID}"]', self.root)
        self.assertRegex(self.root, r'(?m)^\s*Environment\s*=\s*"dev"')
        backend = re.search(r'(?s)backend\s+"s3"\s*\{(.*?)\}', self.root)
        self.assertIsNotNone(backend, "Network root must own an S3 backend")
        self.assertIn(ACCOUNT_ID, backend.group(1))
        self.assertRegex(backend.group(1), r"use_lockfile\s*=\s*true")
        self.assertEqual(list(ROOT.glob(".terraform.lock.hcl")).__len__(), 1)
        self.assertFalse((REPO_ROOT / "infra/accounts/sumak-dev/us-east-1/qa/network").exists())
        self.assertFalse((REPO_ROOT / "infra/accounts/sumak-dev/us-east-1/prod/network").exists())

    def test_dev_root_maps_exact_three_effective_availability_zones(self):
        root = re.search(r'(?s)module\s+"dev_vpc"\s*\{(.*)\n\}', self.root)
        self.assertIsNotNone(root, "Expected the DEV VPC module instance")
        assert root is not None
        zones = re.search(r"(?s)availability_zones\s*=\s*\{(.*?)\n\s{2}\}", root.group(1))
        self.assertIsNotNone(zones, "AZ object map must be declared in the root")
        assert zones is not None
        zone_entries = [(name, body) for name, body in object_entries(zones.group(1))
                        if re.fullmatch(r"us-east-1[a-z]", name)]
        self.assertEqual(len(zone_entries), 3)
        self.assertEqual(
            {name: re.search(r'zone_id\s*=\s*"([^"]+)"', body).group(1)
             for name, body in zone_entries},
            {"us-east-1a": "use1-az2", "us-east-1b": "use1-az4", "us-east-1c": "use1-az6"},
        )
        self.assertIn('vpc_cidr = "10.10.0.0/16"', root.group(1))

    def test_module_expands_three_tiers_across_three_zones_with_unique_cidrs(self):
        tier_blocks = re.search(r"(?s)subnet_tiers\s*=\s*\{(.*?)\n\s{2}\}", self.module)
        self.assertIsNotNone(tier_blocks)
        assert tier_blocks is not None
        tiers = [name for name, _ in object_entries(tier_blocks.group(1))
                 if name in ("public", "application", "data")]
        self.assertCountEqual(tiers, ["public", "application", "data"])
        self.assertRegex(self.module, r"(?s)for\s+zone_name,\s*zone\s+in\s+var\.availability_zones")
        self.assertRegex(self.module, r"(?s)for\s+tier_name,\s*tier\s+in\s+local\.subnet_tiers")
        self.assertRegex(self.module, r"(?s)key\s*=\s*\"\$\{zone_name\}-\$\{tier_name\}\"")
        self.assertEqual(len(blocks(self.module, r'resource\s+"aws_subnet"')), 1)
        self.assertEqual(len(blocks(self.module, r'resource\s+"aws_route_table"')), 1)
        self.assertEqual(len(blocks(self.module, r'resource\s+"aws_route_table_association"')), 1)
        root = re.search(r'(?s)module\s+"dev_vpc"\s*\{(.*?)\n\}', self.root)
        assert root is not None
        cidrs = re.findall(r'(?m)^\s*(?:public_cidr|application_cidr|data_cidr)\s*=\s*"([^"]+)"', root.group(1))
        self.assertEqual(len(cidrs), 9)
        self.assertEqual(len(set(cidrs)), 9, "All nine subnet CIDRs must be unique")
        import ipaddress
        networks = [ipaddress.ip_network(cidr) for cidr in cidrs]
        self.assertTrue(all(network.subnet_of(ipaddress.ip_network("10.10.0.0/16")) for network in networks))

    def test_only_public_subnets_map_public_ips(self):
        subnet = blocks(self.module, r'resource\s+"aws_subnet"')
        self.assertEqual(len(subnet), 1)
        self.assertRegex(subnet[0], r"map_public_ip_on_launch\s*=\s*each\.value\.public_ip")
        tiers = re.search(r"(?s)subnet_tiers\s*=\s*\{(.*?)\n\s{2}\}", self.module)
        assert tiers is not None
        tier_values = [(name, body) for name, body in object_entries(tiers.group(1))
                       if name in ("public", "application", "data")]
        self.assertEqual(len(tier_values), 3)
        by_tier = {name: body for name, body in tier_values}
        self.assertRegex(by_tier["public"], r"public_ip\s*=\s*true")
        self.assertRegex(by_tier["application"], r"public_ip\s*=\s*false")
        self.assertRegex(by_tier["data"], r"public_ip\s*=\s*false")
        self.assertRegex(self.module, r"public_ip\s*=\s*tier\.public_ip")

    def test_igw_and_public_route_supported_but_nat_not_created(self):
        self.assertEqual(len(blocks(self.module, r'resource\s+"aws_internet_gateway"')), 1)
        routes = blocks(self.module, r'resource\s+"aws_route"')
        self.assertEqual(len(routes), 1)
        self.assertIn("aws_internet_gateway.public_ingress.id", routes[0])
        self.assertRegex(routes[0], r"if\s+subnet\.tier\s*==\s*\"public\"")
        self.assertRegex(routes[0], r"for_each\s*=\s*\{")
        for forbidden in ("aws_nat_gateway", "aws_eip"):
            self.assertEqual(blocks(self.module, rf'resource\s+"{forbidden}"'), [])
        for forbidden in ("aws_vpc_peering_connection", "aws_ec2_transit_gateway",
                          "aws_vpn_connection", "aws_vpn_gateway"):
            self.assertEqual(blocks(self.module, rf'resource\s+"{forbidden}"'), [])
        route_tables = blocks(self.module, r'resource\s+"aws_route_table"')
        self.assertEqual(len(route_tables), 1)
        self.assertIn("for_each = local.subnets", route_tables[0])
        self.assertFalse(any("aws_internet_gateway" in b for b in route_tables))


if __name__ == "__main__":
    unittest.main()
