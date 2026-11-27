output "bastion_instance_id" {
  description = "Instance ID passed to AWS Systems Manager Session Manager."
  value       = module.private_ssm_bastion.instance_id
}

output "bastion_private_ip" {
  description = "Private bastion IP address."
  value       = module.private_ssm_bastion.private_ip
}

output "bastion_security_group_id" {
  description = "Security group used by future explicitly authorized management targets."
  value       = module.private_ssm_bastion.security_group_id
}
