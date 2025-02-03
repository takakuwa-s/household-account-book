# https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/cognitive_account
resource "azurerm_cognitive_account" "reciept_recognition" {
  name                          = "${var.config.env}_reciept_recognition"
  location                      = var.config.location
  resource_group_name           = var.resource_group_name
  kind                          = "FormRecognizer"
  public_network_access_enabled = true
  local_auth_enabled            = true

  sku_name = "F0"

  tags = var.default_tags
}