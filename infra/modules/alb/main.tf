locals {
  common_tags = merge(var.tags, {
    ManagedBy = "Terraform"
  })
}

# The ALB is the reviewed public ingress boundary; targets remain private and
# exposure is constrained by the supplied ingress security group and HTTPS listener.
#trivy:ignore:AVD-AWS-0053
resource "aws_lb" "this" {
  name               = var.name
  internal           = false
  load_balancer_type = "application"
  security_groups    = var.security_group_id
  subnets            = var.subnet_ids
  idle_timeout       = var.idle_timeout

  enable_deletion_protection = true
  drop_invalid_header_fields = true

  tags = local.common_tags
}

resource "aws_lb_target_group" "gateway" {
  name                 = "${var.name}-gateway"
  port                 = var.target_port
  protocol             = var.target_protocol
  protocol_version     = "HTTP2"
  vpc_id               = var.vpc_id
  target_type          = "ip"
  deregistration_delay = var.deregistration_delay

  health_check {
    enabled             = true
    path                = var.health_check_path
    port                = "traffic-port"
    protocol            = var.target_protocol
    interval            = var.health_check_interval
    healthy_threshold   = 2
    unhealthy_threshold = 3
    matcher             = "200-399"
  }

  tags = local.common_tags
}

resource "aws_lb_listener" "https" {
  count = var.enable_https_listener ? 1 : 0

  load_balancer_arn = aws_lb.this.arn
  port              = var.listener_port
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = var.certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.gateway.arn
  }
}
