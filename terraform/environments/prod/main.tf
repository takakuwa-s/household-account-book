module "dynamodb" {
  source = "../../modules/aws/dynamodb"
}

module "sqs" {
  source = "../../modules/aws/sqs"
  env    = var.env
}

module "iam" {
  source        = "../../modules/aws/iam"
  env           = var.env
  sqs_arn       = module.sqs.analyse_receipt_queue.arn
  dynamodb_arns = module.dynamodb.dynamodb_arns
}

module "cloudwatch" {
  source = "../../modules/aws/cloudwatch"
  env    = var.env
}

module "lambda" {
  source                    = "../../modules/aws/lambda"
  analyse_receipt_queue     = module.sqs.analyse_receipt_queue
  iam_role_arn              = module.iam.role_arn
  cloudwatch_log_group_name = module.cloudwatch.cloudwatch_log_group_name
  env_variables = {
    env                                 = var.env
    channel_access_token                = var.channel_access_token
    channel_secret                      = var.channel_secret
    azure_document_inteligence_endpoint = var.azure_document_inteligence_endpoint
    azure_key_credential                = var.azure_key_credential
    azure_api_version                   = var.azure_api_version
    spreadsheet_id                      = var.spreadsheet_id
    expenditure_sheet_name              = var.expenditure_sheet_name
  }
}
