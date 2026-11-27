#!/usr/bin/env python3
"""Static security guardrails for the DEV private SSM bastion."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE = REPO_ROOT / "infra/modules/private-ssm-bastion"
ROOT = REPO_ROOT / "infra/accounts/sumak-dev/us-east-1/dev/bastion"


def hcl_blocks(source: str, kind: str) -> list[str]:
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


def read_tf(directory: Path) -> str:
    files = sorted(directory.glob("*.tf"))
    if not files:
        raise AssertionError(f"No Terraform files in {directory}")
    return "\n".join(path.read_text(encoding="utf-8") for path in files)


class DevPrivateSsmBastionBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = read_tf(MODULE)
        cls.root = read_tf(ROOT)

    def test_instance_has_no_public_ip_or_ingress_and_uses_private_subnet(self):
        instances = hcl_blocks(self.module, r'resource\s+"aws_instance"')
        self.assertEqual(len(instances), 1)
        instance = instances[0]
        self.assertRegex(instance, r"associate_public_ip_address\s*=\s*false")
        self.assertRegex(instance, r"subnet_id\s*=\s*var\.subnet_id")
        self.assertIn("subnet_id", self.root)
        self.assertIn("subnet_ids_by_tier.application", self.root)
        ingress = hcl_blocks(self.module, r'resource\s+"aws_vpc_security_group_ingress_rule"')
        self.assertEqual(len(ingress), 1, "Only SSM endpoint TLS ingress is expected")
        self.assertIn("ssm_from_bastion", ingress[0])
        self.assertIn("referenced_security_group_id", ingress[0])
        self.assertRegex(ingress[0], r"from_port\s*=\s*443")
        self.assertNotRegex(self.module, r"(?m)^\s*(?:from_port|to_port)\s*=\s*22\b")

    def test_uses_existing_lab_instance_profile_without_creating_iam(self):
        self.assertRegex(self.module, r"iam_instance_profile\s*=\s*var\.instance_profile_name")
        self.assertRegex(self.module, r'(?s)variable\s+"instance_profile_name"\s*\{.*?default\s*=\s*"LabInstanceProfile"')
        for forbidden in ("aws_iam_role", "aws_iam_instance_profile", "aws_iam_policy",
                          "aws_iam_role_policy", "aws_iam_instance_profile_attachment"):
            self.assertEqual(hcl_blocks(self.module, rf'resource\s+"{forbidden}"'), [])

    def test_root_ebs_is_encrypted_and_capped_at_100_gib(self):
        instance = hcl_blocks(self.module, r'resource\s+"aws_instance"')[0]
        root_volume = re.search(r"(?s)root_block_device\s*\{(.*?)\}", instance)
        self.assertIsNotNone(root_volume)
        assert root_volume is not None
        self.assertRegex(root_volume.group(1), r"encrypted\s*=\s*true")
        self.assertRegex(root_volume.group(1), r"volume_size\s*=\s*var\.root_volume_size_gib")
        self.assertRegex(self.module, r'(?s)variable\s+"root_volume_size_gib"\s*\{.*?default\s*=\s*20')
        self.assertRegex(self.module, r"(?s)variable\s+\"root_volume_size_gib\".*?<=\s*100")

    def test_instance_type_default_and_validation_limit_size_to_large(self):
        self.assertRegex(self.module, r"instance_type\s*=\s*var\.instance_type")
        self.assertRegex(self.module, r'(?s)variable\s+"instance_type"\s*\{.*?default\s*=\s*"t3\.small"')
        self.assertRegex(self.module, r"(?s)variable\s+\"instance_type\".*?nano\|micro\|small\|medium\|large")

    def test_ami_comes_from_ssm_al2023_parameter(self):
        parameters = hcl_blocks(self.module, r'data\s+"aws_ssm_parameter"')
        self.assertEqual(len(parameters), 1)
        self.assertIn("/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64", parameters[0])
        instance = hcl_blocks(self.module, r'resource\s+"aws_instance"')[0]
        self.assertRegex(instance, r"ami\s*=\s*data\.aws_ssm_parameter\.amazon_linux_2023_ami\.value")

    def test_quota_preconditions_include_bastion_and_root_is_dev_only(self):
        instance = hcl_blocks(self.module, r'resource\s+"aws_instance"')[0]
        self.assertRegex(instance, r"existing_running_ec2_count\s*\+\s*1\s*<=\s*9")
        self.assertRegex(instance, r"existing_running_vcpu_count\s*\+\s*2\s*<=\s*32")
        self.assertIn("existing_running_ec2_count", self.root)
        self.assertIn("existing_running_vcpu_count", self.root)
        self.assertIn('allowed_account_ids = ["632080579751"]', self.root)
        self.assertRegex(self.root, r'(?m)^\s*Environment\s*=\s*"dev"')
        self.assertFalse((REPO_ROOT / "infra/accounts/sumak-dev/us-east-1/qa/bastion").exists())
        self.assertFalse((REPO_ROOT / "infra/accounts/sumak-dev/us-east-1/prod/bastion").exists())


if __name__ == "__main__":
    unittest.main()
