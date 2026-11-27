# Application load balancer module

Creates a public, multi-subnet ALB and an HTTP/2 target group for the private
logical gateway. The module reuses an externally managed security group and
does not create DNS, WAF, IAM, VPC, or subnet resources.

The HTTPS listener is disabled by default. Enable it only after an authorized
ACM certificate ARN is available. The idle timeout, health check, target port,
and connection-draining delay are explicit inputs so runtime values can be
reviewed without changing the module.
