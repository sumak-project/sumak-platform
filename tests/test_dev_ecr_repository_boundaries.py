#!/usr/bin/env python3
"""Static security-boundary checks for the DEV service ECR repositories."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE = REPO_ROOT / "infra" / "modules" / "ecr-repository"
ROOT = REPO_ROOT / "infra" / "accounts" / "sumak-dev" / "us-east-1" / "dev" / "ecr"
ACCOUNT_ID = "632080579751"


def resource_blocks(source: str, resource_type: str) -> list[str]:
    marker = re.compile(
        rf'resource\s+"{re.escape(resource_type)}"\s+"[^"]+"\s*\{{'
    )
    blocks: list[str] = []
    for match in marker.finditer(source):
        depth = 1
        for index in range(match.end(), len(source)):
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


class DevEcrRepositoryBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module_main = (MODULE / "main.tf").read_text(encoding="utf-8")
        cls.root_sources = "\n".join(
            path.read_text(encoding="utf-8")
            for path in ROOT.glob("*.tf")
        )

    def test_config_and_identity_services_are_instantiated_for_dev_account(self):
        self.assertIn(f'allowed_account_ids = ["{ACCOUNT_ID}"]', self.root_sources)
        self.assertRegex(self.root_sources, r'Environment\s*=\s*"dev"')
        modules = re.findall(r'module\s+"([^"]+)"', self.root_sources)
        self.assertEqual(modules, ["identity_ecr", "config_ecr"])
        self.assertIn("identity-svc", self.root_sources)
        self.assertIn('repository_name = "sumak/dev/identity-svc"', self.root_sources)
        self.assertIn("config-svc", self.root_sources)
        self.assertIn('repository_name = "sumak/dev/config-svc"', self.root_sources)
        self.assertNotIn("aws_ecr_repository_policy", self.root_sources)
        self.assertNotRegex(self.root_sources, r"(?m)^\s*policy\s*=")

    def test_repository_is_private_immutable_scanned_and_encrypted(self):
        repositories = resource_blocks(self.module_main, "aws_ecr_repository")
        self.assertEqual(len(repositories), 1)
        repository = repositories[0]
        self.assertRegex(repository, r"(?m)^\s*image_tag_mutability\s*=\s*\"IMMUTABLE\"")
        self.assertRegex(repository, r"(?m)^\s*scan_on_push\s*=\s*true")
        self.assertRegex(repository, r"(?m)^\s*encryption_type\s*=\s*\"AES256\"")
        self.assertNotRegex(repository, r"(?m)^\s*encryption_type\s*=\s*\"AES256\"\s*\n\s*kms_key\s*=")

    def test_repository_has_lifecycle_retention_and_prevent_destroy(self):
        policies = resource_blocks(
            self.module_main, "aws_ecr_lifecycle_policy"
        )
        self.assertEqual(len(policies), 1)
        self.assertRegex(policies[0], r"imageCountMoreThan")
        self.assertRegex(policies[0], r"imageCountMoreThan[^\n]*")
        self.assertRegex(policies[0], r"countNumber")
        repositories = resource_blocks(self.module_main, "aws_ecr_repository")
        self.assertRegex(repositories[0], r"(?s)lifecycle\s*\{[^}]*prevent_destroy\s*=\s*true")

    def test_backend_is_account_scoped_with_lockfile_and_lockfile_locking(self):
        backend = re.search(r"(?s)terraform\s*\{.*?backend\s+\"s3\"\s*\{(.*?)\}", self.root_sources)
        self.assertIsNotNone(backend, "Root must configure its own S3 backend")
        assert backend is not None
        self.assertIn(ACCOUNT_ID, backend.group(1))
        self.assertRegex(backend.group(1), r"use_lockfile\s*=\s*true")
        lockfiles = list(ROOT.glob(".terraform.lock.hcl"))
        self.assertEqual(len(lockfiles), 1)

    def test_no_public_or_cross_account_repository_policy(self):
        for forbidden in (
            "aws_ecr_repository_policy",
            "Principal",
            "principal",
            '"*"',
        ):
            self.assertNotIn(forbidden, self.module_main)
        self.assertNotRegex(self.module_main, r"(?m)^\s*public\s*=\s*true")


if __name__ == "__main__":
    unittest.main()
