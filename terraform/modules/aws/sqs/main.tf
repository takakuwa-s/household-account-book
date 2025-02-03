# https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sqs_queue
resource "aws_sqs_queue" "analyse_receipt_queue" {
  name = "${var.env}_analyse_receipt_queue"
}
