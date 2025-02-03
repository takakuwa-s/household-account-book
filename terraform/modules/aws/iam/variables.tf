variable "env" {
  type        = string
  description = "環境名"
}

variable "sqs_arn" {
  type = string
}

variable "dynamodb_arns" {
  type = list(any)
}
