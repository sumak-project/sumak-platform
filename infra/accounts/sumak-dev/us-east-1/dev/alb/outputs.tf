output "alb_arn" {
  description = "DEV application load balancer ARN."
  value       = module.alb.arn
}

output "alb_dns_name" {
  description = "AWS-assigned ALB DNS name; no public DNS authorization is implied."
  value       = module.alb.dns_name
}

output "target_group_arn" {
  description = "DEV logical gateway target group ARN."
  value       = module.alb.target_group_arn
}

output "https_listener_arn" {
  description = "HTTPS listener ARN, null while the certificate dependency is blocked."
  value       = module.alb.https_listener_arn
}
