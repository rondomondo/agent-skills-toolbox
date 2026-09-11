resource "aws_s3_bucket" "webapp" {
  bucket        = "find4-webapp"
  force_destroy = true
}

resource "aws_s3_bucket_website_configuration" "webapp" {
  bucket = aws_s3_bucket.webapp.id

  index_document {
    suffix = "index.html"
  }

  error_document {
    key = "index.html"
  }
}

resource "aws_s3_bucket_public_access_block" "webapp" {
  bucket = aws_s3_bucket.webapp.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_policy" "webapp" {
  bucket = aws_s3_bucket.webapp.id

  # depends_on ensures the public access block is removed before the policy is applied
  depends_on = [aws_s3_bucket_public_access_block.webapp]

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "PublicReadGetObject"
        Effect    = "Allow"
        Principal = "*"
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.webapp.arn}/*"
      }
    ]
  })
}

data "aws_iam_user" "deployer" {
  user_name = "find4-webapp-deployer"
}

resource "aws_iam_user_policy" "deployer" {
  name = "find4-webapp-deploy"
  user = data.aws_iam_user.deployer.user_name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "ListBucket"
        Effect = "Allow"
        Action = ["s3:ListBucket"]
        Resource = aws_s3_bucket.webapp.arn
      },
      {
        Sid    = "ReadWriteObjects"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = "${aws_s3_bucket.webapp.arn}/*"
      }
    ]
  })
}

resource "aws_iam_access_key" "deployer" {
  user = data.aws_iam_user.deployer.user_name
}
