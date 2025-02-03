locals {
  env = "prod"
  default_tags = {
    terraform = "true"
    project   = "household_account_book"
    env       = local.env
  }

  azure_config = {
    location = "japaneast"
    env      = local.env
  }
}

# --------------- Azureのリソース作成 ----------------
module "resource_group" {
  source       = "../../modules/azure/resource_group"
  config       = local.azure_config
  default_tags = local.default_tags
}

module "azurerm_cognitive_account" {
  source              = "../../modules/azure/azurerm_cognitive_account"
  config              = local.azure_config
  default_tags        = local.default_tags
  resource_group_name = module.resource_group.name
}

# --------------- AWSのリソース作成 ----------------

module "dynamodb" {
  source = "../../modules/aws/dynamodb"
}

module "sqs" {
  source = "../../modules/aws/sqs"
  env    = local.env
}

module "iam" {
  source        = "../../modules/aws/iam"
  env           = local.env
  sqs_arn       = module.sqs.analyse_receipt_queue.arn
  dynamodb_arns = module.dynamodb.dynamodb_arns
}

module "cloudwatch" {
  source = "../../modules/aws/cloudwatch"
  env    = local.env
}

module "lambda" {
  source                    = "../../modules/aws/lambda"
  analyse_receipt_queue     = module.sqs.analyse_receipt_queue
  iam_role_arn              = module.iam.role_arn
  cloudwatch_log_group_name = module.cloudwatch.cloudwatch_log_group_name
  env_variables = {
    env                                 = local.env
    channel_access_token                = var.channel_access_token
    channel_secret                      = var.channel_secret
    azure_document_inteligence_endpoint = module.azurerm_cognitive_account.profile.endpoint
    azure_key_credential                = module.azurerm_cognitive_account.profile.key
    spreadsheet_id                      = var.spreadsheet_id
    expenditure_sheet_name              = var.expenditure_sheet_name
  }
}
