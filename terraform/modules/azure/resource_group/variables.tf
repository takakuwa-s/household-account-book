variable "config" {
  type        = map(any)
  description = "Azureの各種設定"
}

variable "default_tags" {
  type        = map(any)
  description = "Azureのリソースに付与するデフォルトのタグ"
}