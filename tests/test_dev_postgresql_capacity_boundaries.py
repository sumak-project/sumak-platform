#!/usr/bin/env python3
"""Static guardrails for the proposed DEV identity/config PostgreSQL capacity."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE = REPO_ROOT / "infra/modules/private-postgresql-capacity"
ROOT = REPO_ROOT / "infra/accounts/sumak-dev/us-east-1/dev/postgresql"


def tf_files(directory: Path) -> dict[str, str]:
    files = sorted(directory.glob("*.tf"))
    if not files:
        raise AssertionError(f"No Terraform files in {directory}")
    return {path.name: path.read_text(encoding="utf-8") for path in files}


class DevPostgresqlCapacityBoundaryTests(unittest.TestCase):
    def test_module_and_dev_root_are_scoped_separately(self):
        self.assertTrue(MODULE.is_dir())
        self.assertTrue(ROOT.is_dir())

    def test_rds_private_encrypted_gp2_and_capacity_bounds(self):
        module = "\n".join(tf_files(MODULE).values())
        self.assertRegex(module, r'aws_db_instance')
        self.assertRegex(module, r"publicly_accessible\s*=\s*false")
        self.assertRegex(module, r"storage_encrypted\s*=\s*true")
        self.assertRegex(module, r"allocated_storage\s*=\s*var\.")
        self.assertRegex(module, r'(?s)variable\s+"allocated_storage".*?<=\s*100')
        self.assertRegex(module, r"storage_type\s*=\s*\"gp2\"")
        self.assertRegex(module, r'(?s)variable\s+"instance_class".*?medium')
        self.assertNotRegex(module, r"monitoring_interval\s*=\s*[1-9]")

    def test_private_multi_az_subnets_and_only_identity_config_ingress(self):
        module = "\n".join(tf_files(MODULE).values())
        root = "\n".join(tf_files(ROOT).values())
        self.assertRegex(module, r"aws_db_subnet_group")
        self.assertRegex(module, r"subnet_ids\s*=\s*var\.private_subnet_ids")
        self.assertRegex(module, r"length\(var\.private_subnet_ids\)\s*>=\s*2")
        self.assertRegex(module, r"aws_vpc_security_group_ingress_rule")
        for source in (module, root):
            self.assertIn("identity", source.lower())
            self.assertIn("config", source.lower())
        self.assertRegex(module, r"referenced_security_group_id")
        self.assertRegex(module, r"from_port\s*=\s*5432")
        self.assertNotRegex(module, r"cidr_ipv4\s*=\s*\"0\.0\.0\.0/0\"")

    def test_tls_deletion_protection_snapshot_and_secret_credentials(self):
        module = "\n".join(tf_files(MODULE).values())
        self.assertRegex(module, r"rds.force_ssl")
        self.assertRegex(module, r"deletion_protection\s*=\s*true")
        self.assertRegex(module, r"skip_final_snapshot\s*=\s*false")
        self.assertRegex(module, r"final_snapshot_identifier")
        self.assertRegex(module, r"aws_secretsmanager_secret")
        self.assertRegex(module, r"manage_master_user_password\s*=\s*true")
        self.assertNotRegex(module, r'(?m)^\s*password\s*=\s*"[^"]+"')

    def test_backend_is_same_account_locked_and_bootstrap_owns_exact_databases(self):
        root_files = tf_files(ROOT)
        root = "\n".join(root_files.values())
        backend = re.search(r'(?s)terraform\s*\{.*?backend\s+"s3"\s*\{(.*?)\}', root)
        self.assertIsNotNone(backend, "DEV root must configure its S3 state backend")
        assert backend is not None
        self.assertRegex(backend.group(1), r"use_lockfile\s*=\s*true")
        self.assertRegex(backend.group(1), r"632080579751")
        self.assertRegex(root, r'allowed_account_ids\s*=\s*\["632080579751"\]')
        sql = "\n".join(
            content for name, content in root_files.items()
            if name.endswith(".tf") and ("bootstrap" in content.lower() or "sumak_identity" in content)
        )
        if not sql:
            sql_files = [p.read_text(encoding="utf-8") for p in ROOT.rglob("*.sql")]
            sql = "\n".join(sql_files)
        self.assertTrue(sql, "Expected generated bootstrap SQL or equivalent database ownership declaration")
        databases = set(re.findall(r"\bsumak_[a-z0-9_]+\b", sql))
        self.assertEqual(databases, {"sumak_identity", "sumak_config"})


if __name__ == "__main__":
    unittest.main()
