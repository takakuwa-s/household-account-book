variable "channel_access_token" {
  type        = string
  description = "LINE Botのチャンネルアクセストークン"
}

variable "channel_secret" {
  type        = string
  description = "LINE Botのチャンネルシークレット"
}

variable "azure_subscription_id" {
  type        = string
  description = "AzureのサブスクリプションID"
}

variable "spreadsheet_id" {
  type        = string
  description = "レシート解析結果を書き出すスプレッドシートのID"
}

variable "expenditure_sheet_name" {
  type        = string
  description = "レシート解析結果を書き出すスプレッドシートのシート名"
}
