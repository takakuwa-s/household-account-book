# https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/dynamodb_table_item
resource "aws_dynamodb_table_item" "table_items" {
  for_each = var.items

  table_name = var.table_name
  hash_key   = var.hash_key
  range_key  = var.range_key

  item = jsonencode(each.value)
}
