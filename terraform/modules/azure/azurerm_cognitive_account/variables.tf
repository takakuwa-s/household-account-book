variable "resource_group_name" {
  type        = string
  description = "Azureのリソースグループ名"
}

variable "config" {
  type        = map(any)
  description = "Azureの各種設定"
}

variable "default_tags" {
  type        = map(any)
  description = "Azureのリソースに付与するデフォルトのタグ"
}