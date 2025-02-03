# https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/resource_group
resource "azurerm_resource_group" "household_account_book" {
  name     = "${var.config.env}_household_account_book"
  location = var.config.location
  tags     = var.default_tags
}