locals {
  cf_origin_id  = "find4-webapp-s3"
  cert_arn      = "arn:aws:acm:us-east-1:829369163988:certificate/c468b859-cb3d-453d-bdef-7f14fe9271a2"
  custom_domain = "find4.org"
}

resource "aws_cloudfront_distribution" "webapp" {
  comment             = "find4-webapp"
  enabled             = true
  default_root_object = "index.html"
  price_class         = "PriceClass_100"
  aliases             = [local.custom_domain]

  origin {
    origin_id   = local.cf_origin_id
    domain_name = aws_s3_bucket_website_configuration.webapp.website_endpoint

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "http-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  default_cache_behavior {
    target_origin_id       = local.cf_origin_id
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    compress               = true

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    min_ttl     = 0
    default_ttl = 0
    max_ttl     = 0
  }

  viewer_certificate {
    acm_certificate_arn      = local.cert_arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }
}
