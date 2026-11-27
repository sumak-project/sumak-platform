# Private ECR repositories

This module creates private, encrypted ECR repositories within one AWS account
and environment. Tags are immutable, image scanning runs on push, and only a
configurable maximum number of images is retained.

The module deliberately creates no repository policy. Access remains governed
by the same-account IAM identities approved for the environment; callers must
not infer push permission for `LabRole` or cross-account access.

Repositories are protected with `prevent_destroy`. Removing one requires an
explicit, reviewed lifecycle change and confirmation that its immutable image
digests are no longer needed.
