locals {
  dynamodb_tables = yamldecode(file("../../modules/aws/dynamodb/dynamodb_tables.yml"))
}

# https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/dynamodb_table
resource "aws_dynamodb_table" "dynamodb_tables" {
  for_each = local.dynamodb_tables

  name           = each.key
  billing_mode   = "PROVISIONED"
  read_capacity  = 5
  write_capacity = 5
  hash_key       = each.value.hash_key
  range_key      = lookup(each.value, "range_key", null)

  dynamic "attribute" {
    for_each = each.value.attributes
    content {
      name = attribute.value.name
      type = attribute.value.type
    }
  }

  server_side_encryption {
    enabled = true
  }

  ttl {
    attribute_name = "ttl_timestamp"
    enabled        = true
  }
}


module "table_items" {
  source     = "./table_items"
  for_each   = { for key, value in local.dynamodb_tables : key => value if contains(keys(value), "items") }
  table_name = each.value.name
  hash_key   = each.value.hash_key
  range_key  = lookup(each.value, "range_key", null)
  items      = each.value.items
  depends_on = [aws_dynamodb_table.dynamodb_tables]
}
