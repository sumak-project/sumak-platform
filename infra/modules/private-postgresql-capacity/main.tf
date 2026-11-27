locals {
  common_tags = merge(var.tags, {
    ManagedBy = "Terraform"
    Tier      = "data"
  })
}

resource "aws_db_subnet_group" "this" {
  name       = var.name
  subnet_ids = var.private_subnet_ids
  tags       = local.common_tags
}

resource "aws_security_group" "this" {
  name        = "${var.name}-postgresql"
  description = "Private PostgreSQL access for the identity and config owners only."
  vpc_id      = var.vpc_id
  tags        = local.common_tags
}

resource "aws_vpc_security_group_ingress_rule" "owner" {
  for_each = var.owner_security_group_ids

  security_group_id            = aws_security_group.this.id
  referenced_security_group_id = each.value
  description                  = "${each.key} service to its owned PostgreSQL database."
  from_port                    = 5432
  to_port                      = 5432
  ip_protocol                  = "tcp"
}

resource "aws_db_parameter_group" "this" {
  name   = "${var.name}-postgres16"
  family = "postgres16"

  parameter {
    name         = "rds.force_ssl"
    value        = "1"
    apply_method = "immediate"
  }

  tags = local.common_tags
}

resource "aws_db_instance" "this" {
  identifier = var.name

  engine         = "postgres"
  engine_version = var.engine_version
  instance_class = var.instance_class

  allocated_storage = var.allocated_storage
  storage_type      = "gp2"
  storage_encrypted = true

  username                    = "sumak_admin"
  manage_master_user_password = true
  port                        = 5432

  db_subnet_group_name   = aws_db_subnet_group.this.name
  parameter_group_name   = aws_db_parameter_group.this.name
  vpc_security_group_ids = [aws_security_group.this.id]
  publicly_accessible    = false
  multi_az               = false

  auto_minor_version_upgrade = true
  backup_retention_period    = 1
  copy_tags_to_snapshot      = true

  deletion_protection       = true
  skip_final_snapshot       = false
  final_snapshot_identifier = "${var.name}-final"

  tags = local.common_tags
}

resource "aws_secretsmanager_secret" "owner_credentials" {
  for_each = toset([
    "identity-runtime",
    "identity-migration",
    "config-runtime",
    "config-migration",
  ])

  name                    = "${var.name}/${each.value}"
  description             = "Credential placeholder populated through the authorized database bootstrap procedure."
  recovery_window_in_days = 7
  tags                    = merge(local.common_tags, { Owner = split("-", each.value)[0] })
}
