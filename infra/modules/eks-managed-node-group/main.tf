locals {
  common_tags = merge(var.tags, {
    ManagedBy = "Terraform"
  })
}

resource "aws_launch_template" "nodes" {
  name_prefix            = "${var.name}-"
  update_default_version = true

  block_device_mappings {
    device_name = "/dev/xvda"

    ebs {
      delete_on_termination = true
      encrypted             = true
      volume_size           = var.root_volume_size
      volume_type           = "gp2"
    }
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_protocol_ipv6          = "disabled"
    http_put_response_hop_limit = 2
    http_tokens                 = "required"
  }

  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags          = local.common_tags
  }

  tag_specifications {
    resource_type = "volume"
    tags          = local.common_tags
  }

  tags = local.common_tags
}

resource "aws_eks_node_group" "this" {
  cluster_name    = var.cluster_name
  node_group_name = var.name
  node_role_arn   = var.node_role_arn
  subnet_ids      = var.subnet_ids
  instance_types  = ["t3.large"]
  capacity_type   = "ON_DEMAND"

  scaling_config {
    min_size     = 3
    desired_size = 3
    max_size     = 3
  }

  update_config {
    max_unavailable = 1
  }

  launch_template {
    id      = aws_launch_template.nodes.id
    version = aws_launch_template.nodes.latest_version
  }

  tags = local.common_tags

  lifecycle {
    precondition {
      condition     = length(var.availability_zones) == length(var.subnet_ids)
      error_message = "Each private subnet must have one corresponding availability zone."
    }
  }
}
