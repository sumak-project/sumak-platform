data "aws_region" "current" {}

resource "aws_security_group" "endpoints" {
  name_prefix = "${var.name}-endpoints-"
  description = "Allow private HTTPS access to required AWS service endpoints"
  vpc_id      = var.vpc_id

  ingress {
    description = "HTTPS from the DEV VPC"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr_block]
  }

  tags = merge(var.tags, {
    Name = "${var.name}-aws-api-endpoints"
  })

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_vpc_endpoint" "interface" {
  for_each = toset(["ec2", "ecr.api", "ecr.dkr"])

  vpc_id              = var.vpc_id
  service_name        = "com.amazonaws.${data.aws_region.current.region}.${each.value}"
  vpc_endpoint_type   = "Interface"
  private_dns_enabled = true
  subnet_ids          = var.subnet_ids
  security_group_ids  = [aws_security_group.endpoints.id]

  tags = merge(var.tags, {
    Name = "${var.name}-${replace(each.value, ".", "-")}"
  })
}

resource "aws_vpc_endpoint" "s3" {
  vpc_id            = var.vpc_id
  service_name      = "com.amazonaws.${data.aws_region.current.region}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = var.route_table_ids

  tags = merge(var.tags, {
    Name = "${var.name}-s3"
  })
}
