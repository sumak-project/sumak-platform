output "arn" {
  description = "Application load balancer ARN."
  value       = aws_lb.this.arn
}

output "dns_name" {
  description = "AWS-assigned load balancer DNS name; not an authorized public domain."
  value       = aws_lb.this.dns_name
}

output "zone_id" {
  description = "Canonical hosted zone ID of the load balancer."
  value       = aws_lb.this.zone_id
}

output "target_group_arn" {
  description = "Logical gateway target group ARN."
  value       = aws_lb_target_group.gateway.arn
}

output "https_listener_arn" {
  description = "HTTPS listener ARN, or null while certificate authorization is blocked."
  value       = try(aws_lb_listener.https[0].arn, null)
}
