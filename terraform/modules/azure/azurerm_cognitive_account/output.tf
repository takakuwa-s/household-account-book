output "profile" {
  value = {
    endpoint = azurerm_cognitive_account.reciept_recognition.endpoint
    key      = azurerm_cognitive_account.reciept_recognition.primary_access_key
  }
}
