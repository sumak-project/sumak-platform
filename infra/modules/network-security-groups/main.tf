locals {
  common_tags = merge(var.tags, {
    ManagedBy = "Terraform"
  })

  bff_security_group_ids = {
    admin  = aws_security_group.admin_bff.id
    mobile = aws_security_group.mobile_bff.id
  }

  bff_service_flows = {
    for flow in flatten([
      for service_name, service in var.services : [
        for bff in service.allowed_bffs : {
          key          = "${bff}-${service_name}"
          bff          = bff
          service_name = service_name
          port         = service.grpc_port
        }
      ]
    ]) : flow.key => flow
  }

  service_databases = {
    for service_name, service in var.services :
    service_name => service if service.database_port != null
  }

  service_broker_flows = {
    for flow in flatten([
      for broker_name, broker in var.brokers : [
        for service_name in broker.allowed_services : {
          key          = "${service_name}-${broker_name}"
          service_name = service_name
          broker_name  = broker_name
          port         = broker.tls_port
        }
      ]
    ]) : flow.key => flow
  }
}

resource "aws_security_group" "alb" {
  name        = "${var.name_prefix}-alb"
  description = "Public ingress terminator; forwards only to the logical gateway."
  vpc_id      = var.vpc_id
  tags        = merge(local.common_tags, { Tier = "ingress" })
}

resource "aws_security_group" "gateway" {
  name        = "${var.name_prefix}-gateway"
  description = "Logical API gateway between the ALB and the BFF tier."
  vpc_id      = var.vpc_id
  tags        = merge(local.common_tags, { Tier = "application" })
}

resource "aws_security_group" "mobile_bff" {
  name        = "${var.name_prefix}-mobile-bff"
  description = "Mobile BFF with explicit service-level gRPC access."
  vpc_id      = var.vpc_id
  tags        = merge(local.common_tags, { Tier = "application" })
}

resource "aws_security_group" "admin_bff" {
  name        = "${var.name_prefix}-admin-bff"
  description = "Administrative BFF with explicit service-level gRPC access."
  vpc_id      = var.vpc_id
  tags        = merge(local.common_tags, { Tier = "application" })
}

resource "aws_security_group" "service" {
  for_each = var.services

  name        = "${var.name_prefix}-${each.key}-service"
  description = "Private ${each.key} service; accepts only approved BFF gRPC flows."
  vpc_id      = var.vpc_id
  tags        = merge(local.common_tags, { Tier = "application", Owner = each.key })
}

resource "aws_security_group" "database" {
  for_each = local.service_databases

  name        = "${var.name_prefix}-${each.key}-database"
  description = "Private database owned exclusively by the ${each.key} service."
  vpc_id      = var.vpc_id
  tags        = merge(local.common_tags, { Tier = "data", Owner = each.key })
}

resource "aws_security_group" "broker" {
  for_each = var.brokers

  name        = "${var.name_prefix}-${each.key}-broker"
  description = "Private ${each.key} broker listener with explicit service callers."
  vpc_id      = var.vpc_id
  tags        = merge(local.common_tags, { Tier = "data", Owner = each.key })
}

resource "aws_security_group" "ssm_bastion" {
  name        = "${var.name_prefix}-ssm-bastion"
  description = "Private SSM bastion; no inbound network rules or public SSH."
  vpc_id      = var.vpc_id
  tags        = merge(local.common_tags, { Tier = "management" })
}

resource "aws_security_group" "management_endpoint" {
  for_each = var.management_endpoints

  name        = "${var.name_prefix}-${each.key}-management"
  description = "Private ${each.key} administrative endpoint reachable only through the SSM bastion."
  vpc_id      = var.vpc_id
  tags        = merge(local.common_tags, { Tier = "management" })
}

resource "aws_vpc_security_group_ingress_rule" "alb_ipv4" {
  for_each = var.allowed_ingress_ipv4_cidrs

  security_group_id = aws_security_group.alb.id
  description       = "Reviewed IPv4 origin to ALB TLS/WSS listener."
  cidr_ipv4         = each.value
  from_port         = var.alb_listener_port
  to_port           = var.alb_listener_port
  ip_protocol       = "tcp"
}

resource "aws_vpc_security_group_ingress_rule" "alb_ipv6" {
  for_each = var.allowed_ingress_ipv6_cidrs

  security_group_id = aws_security_group.alb.id
  description       = "Reviewed IPv6 origin to ALB TLS/WSS listener."
  cidr_ipv6         = each.value
  from_port         = var.alb_listener_port
  to_port           = var.alb_listener_port
  ip_protocol       = "tcp"
}

resource "aws_vpc_security_group_egress_rule" "alb_to_gateway" {
  security_group_id            = aws_security_group.alb.id
  description                  = "ALB to logical gateway over the reviewed TLS port."
  referenced_security_group_id = aws_security_group.gateway.id
  from_port                    = var.gateway_port
  to_port                      = var.gateway_port
  ip_protocol                  = "tcp"
}

resource "aws_vpc_security_group_ingress_rule" "gateway_from_alb" {
  security_group_id            = aws_security_group.gateway.id
  description                  = "Logical gateway accepts traffic only from the ALB."
  referenced_security_group_id = aws_security_group.alb.id
  from_port                    = var.gateway_port
  to_port                      = var.gateway_port
  ip_protocol                  = "tcp"
}

resource "aws_vpc_security_group_egress_rule" "gateway_to_bff" {
  for_each = local.bff_security_group_ids

  security_group_id            = aws_security_group.gateway.id
  description                  = "Logical gateway to the ${each.key} BFF."
  referenced_security_group_id = each.value
  from_port                    = var.bff_port
  to_port                      = var.bff_port
  ip_protocol                  = "tcp"
}

resource "aws_vpc_security_group_ingress_rule" "bff_from_gateway" {
  for_each = local.bff_security_group_ids

  security_group_id            = each.value
  description                  = "${each.key} BFF accepts traffic only from the logical gateway."
  referenced_security_group_id = aws_security_group.gateway.id
  from_port                    = var.bff_port
  to_port                      = var.bff_port
  ip_protocol                  = "tcp"
}

resource "aws_vpc_security_group_egress_rule" "bff_to_service" {
  for_each = local.bff_service_flows

  security_group_id            = local.bff_security_group_ids[each.value.bff]
  description                  = "${each.value.bff} BFF to ${each.value.service_name} gRPC service."
  referenced_security_group_id = aws_security_group.service[each.value.service_name].id
  from_port                    = each.value.port
  to_port                      = each.value.port
  ip_protocol                  = "tcp"
}

resource "aws_vpc_security_group_ingress_rule" "service_from_bff" {
  for_each = local.bff_service_flows

  security_group_id            = aws_security_group.service[each.value.service_name].id
  description                  = "${each.value.service_name} service accepts gRPC only from the ${each.value.bff} BFF."
  referenced_security_group_id = local.bff_security_group_ids[each.value.bff]
  from_port                    = each.value.port
  to_port                      = each.value.port
  ip_protocol                  = "tcp"
}

resource "aws_vpc_security_group_egress_rule" "service_to_database" {
  for_each = local.service_databases

  security_group_id            = aws_security_group.service[each.key].id
  description                  = "${each.key} service to its owned database."
  referenced_security_group_id = aws_security_group.database[each.key].id
  from_port                    = each.value.database_port
  to_port                      = each.value.database_port
  ip_protocol                  = "tcp"
}

resource "aws_vpc_security_group_ingress_rule" "database_from_owner" {
  for_each = local.service_databases

  security_group_id            = aws_security_group.database[each.key].id
  description                  = "${each.key} database accepts traffic only from its owning service."
  referenced_security_group_id = aws_security_group.service[each.key].id
  from_port                    = each.value.database_port
  to_port                      = each.value.database_port
  ip_protocol                  = "tcp"
}

resource "aws_vpc_security_group_egress_rule" "service_to_broker" {
  for_each = local.service_broker_flows

  security_group_id            = aws_security_group.service[each.value.service_name].id
  description                  = "${each.value.service_name} service to the ${each.value.broker_name} broker TLS listener."
  referenced_security_group_id = aws_security_group.broker[each.value.broker_name].id
  from_port                    = each.value.port
  to_port                      = each.value.port
  ip_protocol                  = "tcp"
}

resource "aws_vpc_security_group_ingress_rule" "broker_from_service" {
  for_each = local.service_broker_flows

  security_group_id            = aws_security_group.broker[each.value.broker_name].id
  description                  = "${each.value.broker_name} broker accepts traffic from ${each.value.service_name} only."
  referenced_security_group_id = aws_security_group.service[each.value.service_name].id
  from_port                    = each.value.port
  to_port                      = each.value.port
  ip_protocol                  = "tcp"
}

resource "aws_vpc_security_group_egress_rule" "bastion_to_management" {
  for_each = var.management_endpoints

  security_group_id            = aws_security_group.ssm_bastion.id
  description                  = "SSM bastion to the ${each.key} private administrative endpoint."
  referenced_security_group_id = aws_security_group.management_endpoint[each.key].id
  from_port                    = each.value.port
  to_port                      = each.value.port
  ip_protocol                  = "tcp"
}

resource "aws_vpc_security_group_ingress_rule" "management_from_bastion" {
  for_each = var.management_endpoints

  security_group_id            = aws_security_group.management_endpoint[each.key].id
  description                  = "${each.key} administrative endpoint accepts traffic only from the SSM bastion."
  referenced_security_group_id = aws_security_group.ssm_bastion.id
  from_port                    = each.value.port
  to_port                      = each.value.port
  ip_protocol                  = "tcp"
}
