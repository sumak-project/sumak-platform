locals {
  common_tags = merge(var.tags, {
    ManagedBy = "Terraform"
  })

  subnet_tiers = {
    public = {
      cidr_attribute = "public_cidr"
      public_ip      = true
    }
    application = {
      cidr_attribute = "application_cidr"
      public_ip      = false
    }
    data = {
      cidr_attribute = "data_cidr"
      public_ip      = false
    }
  }

  subnets = {
    for subnet in flatten([
      for zone_name, zone in var.availability_zones : [
        for tier_name, tier in local.subnet_tiers : {
          key        = "${zone_name}-${tier_name}"
          zone_name  = zone_name
          zone_id    = zone.zone_id
          tier       = tier_name
          cidr_block = zone[tier.cidr_attribute]
          public_ip  = tier.public_ip
        }
      ]
    ]) : subnet.key => subnet
  }
}

resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(local.common_tags, {
    Name = var.name
  })

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_internet_gateway" "public_ingress" {
  vpc_id = aws_vpc.this.id

  tags = merge(local.common_tags, {
    Name = "${var.name}-public-ingress"
    Tier = "public"
  })
}

# Only entries explicitly modeled as the public ingress tier receive public IPs;
# application and data subnet entries keep public_ip=false.
#trivy:ignore:AVD-AWS-0164
resource "aws_subnet" "this" {
  for_each = local.subnets

  vpc_id                  = aws_vpc.this.id
  availability_zone_id    = each.value.zone_id
  cidr_block              = each.value.cidr_block
  map_public_ip_on_launch = each.value.public_ip

  tags = merge(local.common_tags, {
    Name             = "${var.name}-${each.key}"
    Tier             = each.value.tier
    AvailabilityZone = each.value.zone_name
    PhysicalZoneId   = each.value.zone_id
  })
}

resource "aws_route_table" "this" {
  for_each = local.subnets

  vpc_id = aws_vpc.this.id

  tags = merge(local.common_tags, {
    Name             = "${var.name}-${each.key}"
    Tier             = each.value.tier
    AvailabilityZone = each.value.zone_name
  })
}

resource "aws_route" "public_ipv4" {
  for_each = {
    for key, subnet in local.subnets : key => subnet
    if subnet.tier == "public"
  }

  route_table_id         = aws_route_table.this[each.key].id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.public_ingress.id
}

resource "aws_route_table_association" "this" {
  for_each = aws_subnet.this

  subnet_id      = each.value.id
  route_table_id = aws_route_table.this[each.key].id
}
