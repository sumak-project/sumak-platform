locals {
  common_tags = merge(var.tags, {
    ManagedBy = "Terraform"
  })

  ssm_endpoint_services = toset([
    "ec2messages",
    "ssm",
    "ssmmessages",
  ])
}

data "aws_ssm_parameter" "amazon_linux_2023_ami" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
}

resource "aws_security_group" "bastion" {
  name        = "${var.name}-bastion"
  description = "Private SSM bastion with no inbound network access."
  vpc_id      = var.vpc_id

  tags = merge(local.common_tags, {
    Name = "${var.name}-bastion"
    Tier = "management"
  })
}

resource "aws_security_group" "ssm_endpoints" {
  name        = "${var.name}-ssm-endpoints"
  description = "Private SSM endpoints reachable only from the bastion."
  vpc_id      = var.vpc_id

  tags = merge(local.common_tags, {
    Name = "${var.name}-ssm-endpoints"
    Tier = "management"
  })
}

resource "aws_vpc_security_group_egress_rule" "bastion_to_ssm" {
  security_group_id            = aws_security_group.bastion.id
  description                  = "Bastion TLS access to private SSM endpoints."
  referenced_security_group_id = aws_security_group.ssm_endpoints.id
  from_port                    = 443
  to_port                      = 443
  ip_protocol                  = "tcp"
}

resource "aws_vpc_security_group_ingress_rule" "ssm_from_bastion" {
  security_group_id            = aws_security_group.ssm_endpoints.id
  description                  = "Private SSM endpoint TLS from the bastion only."
  referenced_security_group_id = aws_security_group.bastion.id
  from_port                    = 443
  to_port                      = 443
  ip_protocol                  = "tcp"
}

resource "aws_vpc_endpoint" "ssm" {
  for_each = local.ssm_endpoint_services

  vpc_id              = var.vpc_id
  service_name        = "com.amazonaws.${data.aws_region.current.region}.${each.key}"
  vpc_endpoint_type   = "Interface"
  private_dns_enabled = true
  subnet_ids          = var.private_subnet_ids
  security_group_ids  = [aws_security_group.ssm_endpoints.id]

  tags = merge(local.common_tags, {
    Name = "${var.name}-${each.key}"
  })
}

data "aws_region" "current" {}

resource "aws_instance" "bastion" {
  ami                         = data.aws_ssm_parameter.amazon_linux_2023_ami.value
  instance_type               = var.instance_type
  subnet_id                   = var.subnet_id
  associate_public_ip_address = false
  iam_instance_profile        = var.instance_profile_name
  vpc_security_group_ids      = [aws_security_group.bastion.id]
  monitoring                  = true

  metadata_options {
    http_endpoint = "enabled"
    http_tokens   = "required"
  }

  root_block_device {
    encrypted   = true
    volume_size = var.root_volume_size_gib
    volume_type = "gp3"
  }

  lifecycle {
    precondition {
      condition     = var.existing_running_ec2_count + 1 <= 9
      error_message = "Adding the bastion would exceed the nine-running-EC2 Learner Lab boundary."
    }

    precondition {
      condition     = var.existing_running_vcpu_count + 2 <= 32
      error_message = "Adding the two-vCPU bastion would exceed the 32-vCPU regional boundary."
    }
  }

  depends_on = [aws_vpc_endpoint.ssm]

  tags = merge(local.common_tags, {
    Name = "${var.name}-bastion"
    Tier = "management"
  })
}
