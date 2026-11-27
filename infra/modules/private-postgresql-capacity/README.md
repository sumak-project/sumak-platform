# Private PostgreSQL capacity

Creates one private, encrypted PostgreSQL RDS instance, its data subnet group,
TLS parameter group, restricted security group, an AWS-managed administrator
credential, and owner credential placeholders.

Database and role creation is deliberately not performed by a Terraform
PostgreSQL provider: the endpoint is private and bootstrap must run through an
authorized administrative path. Populate the placeholders only after executing
and validating the reviewed bootstrap procedure.
