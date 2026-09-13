data "aws_route53_zone" "find4" {
  zone_id = "Z02019123IH7MLXLJZV8M"
}

resource "aws_route53_record" "find4_root" {
  zone_id = data.aws_route53_zone.find4.zone_id
  name    = "find4.org"
  type    = "A"

  alias {
    name                   = aws_cloudfront_distribution.webapp.domain_name
    zone_id                = aws_cloudfront_distribution.webapp.hosted_zone_id
    evaluate_target_health = false
  }
}

resource "aws_route53_record" "find4_root_aaaa" {
  zone_id = data.aws_route53_zone.find4.zone_id
  name    = "find4.org"
  type    = "AAAA"

  alias {
    name                   = aws_cloudfront_distribution.webapp.domain_name
    zone_id                = aws_cloudfront_distribution.webapp.hosted_zone_id
    evaluate_target_health = false
  }
}
