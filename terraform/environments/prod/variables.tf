variable "env" {
  type        = string
  description = "環境名"
  default     = "prod"
}

variable "channel_access_token" {
  type        = string
  description = "LINE Botのチャンネルアクセストークン"
}

variable "channel_secret" {
  type        = string
  description = "LINE Botのチャンネルシークレット"
}


variable "azure_document_inteligence_endpoint" {
  type        = string
  description = "AzureのDocument Intelligenceのエンドポイント"
}


variable "azure_key_credential" {
  type    = string
  default = "AzureのDocument Intelligence APIを利用するためのキー"
}


variable "azure_api_version" {
  type        = string
  description = "AzureのDocument IntelligenceのAPIバージョン"
}


variable "spreadsheet_id" {
  type        = string
  description = "レシート解析結果を書き出すスプレッドシートのID"
}

variable "expenditure_sheet_name" {
  type        = string
  description = "レシート解析結果を書き出すスプレッドシートのシート名"
}
