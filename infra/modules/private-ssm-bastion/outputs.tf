output "instance_id" {
  description = "Private bastion instance ID used to start SSM sessions."
  value       = aws_instance.bastion.id
}

output "private_ip" {
  description = "Private bastion IP address."
  value       = aws_instance.bastion.private_ip
}

output "security_group_id" {
  description = "Security group used to authorize explicit private management flows."
  value       = aws_security_group.bastion.id
}

output "ssm_endpoint_ids" {
  description = "Private interface endpoint IDs used by the SSM agent."
  value       = { for name, endpoint in aws_vpc_endpoint.ssm : name => endpoint.id }
}
