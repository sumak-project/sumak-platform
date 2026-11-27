output "security_group_ids" {
  description = "Managed security group IDs by tier and owner."
  value = {
    alb                  = aws_security_group.alb.id
    gateway              = aws_security_group.gateway.id
    mobile_bff           = aws_security_group.mobile_bff.id
    admin_bff            = aws_security_group.admin_bff.id
    services             = { for name, group in aws_security_group.service : name => group.id }
    databases            = { for name, group in aws_security_group.database : name => group.id }
    brokers              = { for name, group in aws_security_group.broker : name => group.id }
    ssm_bastion          = aws_security_group.ssm_bastion.id
    management_endpoints = { for name, group in aws_security_group.management_endpoint : name => group.id }
  }
}
