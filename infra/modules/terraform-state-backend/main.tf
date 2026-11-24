resource "awscc_s3_bucket" "this" {
  bucket_name = var.bucket_name

  bucket_encryption = {
    server_side_encryption_configuration = [{
      bucket_key_enabled = false
      server_side_encryption_by_default = {
        sse_algorithm = "AES256"
      }
    }]
  }

  ownership_controls = {
    rules = [{
      object_ownership = "BucketOwnerEnforced"
    }]
  }

  public_access_block_configuration = {
    block_public_acls       = true
    block_public_policy     = true
    ignore_public_acls      = true
    restrict_public_buckets = true
  }

  tags = [for key, value in var.tags : {
    key   = key
    value = value
  }]

  versioning_configuration = {
    status = "Enabled"
  }

  lifecycle {
    prevent_destroy = true
  }
}

data "aws_iam_policy_document" "this" {
  statement {
    sid    = "DenyInsecureTransport"
    effect = "Deny"

    principals {
      type        = "*"
      identifiers = ["*"]
    }

    actions = ["s3:*"]

    resources = [
      awscc_s3_bucket.this.arn,
      "${awscc_s3_bucket.this.arn}/*",
    ]

    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }
}

resource "aws_s3_bucket_policy" "this" {
  bucket = awscc_s3_bucket.this.bucket_name
  policy = data.aws_iam_policy_document.this.json
}
