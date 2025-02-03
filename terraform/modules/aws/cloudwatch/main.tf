# https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_log_group
resource "aws_cloudwatch_log_group" "lambda_log_group" {
  name              = "${var.env}_lambda_log_group"
  retention_in_days = 30
}
