output "dynamodb_arns" {
  value = [for table in aws_dynamodb_table.dynamodb_tables : table.arn]
}
