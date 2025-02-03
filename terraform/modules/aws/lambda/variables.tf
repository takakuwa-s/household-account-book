variable "iam_role_arn" {
  type = string
}

variable "cloudwatch_log_group_name" {
  type = string
}

variable "analyse_receipt_queue" {
  type = object({
    id       = string
    arn      = string
    tags_all = map(any)
    url      = string
  })
}

variable "env_variables" {
  description = "環境変数"
  type = object({
    env                                 = string
    channel_access_token                = string
    channel_secret                      = string
    azure_document_inteligence_endpoint = string
    azure_key_credential                = string
    azure_api_version                   = string
    spreadsheet_id                      = string
    expenditure_sheet_name              = string
  })

}
