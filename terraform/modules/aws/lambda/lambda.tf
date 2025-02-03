locals {
  lambda_functions = yamldecode(file("../../modules/aws/lambda/lambda_functions.yml"))
}

# https://registry.terraform.io/providers/hashicorp/archive/latest/docs/data-sources/file
data "archive_file" "python_code_zip" {
  type        = "zip"
  source_dir  = "../../../"
  output_path = "../../output/python_code.zip"
  excludes = [
    "terraform/**",
    "requirements.txt",
    ".env",
    ".git/**",
    ".DS_Store",
    ".gitignore",
    "**/.pytest_cache/**",
    "**/__pycache__/**",
    "**/.ruff_cache/**",
    ".venv/**",
    "**.zip",
    "**.md",
  ]
}

# https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function
resource "aws_lambda_function" "lambda_functions" {
  for_each = local.lambda_functions

  function_name    = "${var.env_variables.env}_${each.key}"
  filename         = data.archive_file.python_code_zip.output_path
  source_code_hash = data.archive_file.python_code_zip.output_base64sha256
  runtime          = "python3.12"
  role             = var.iam_role_arn
  handler          = each.value.handler
  memory_size      = each.value.memory_size
  timeout          = each.value.timeout
  architectures    = ["arm64"]
  layers           = [aws_lambda_layer_version.pip_package_layer.arn]

  logging_config {
    log_format       = "JSON"
    log_group        = var.cloudwatch_log_group_name
    system_log_level = "INFO"
  }

  environment {
    variables = {
      # LINE Bot関連
      CHANNEL_ACCESS_TOKEN = var.env_variables.channel_access_token
      CHANNEL_SECRET       = var.env_variables.channel_secret

      # AZURE関連
      AZURE_DOCUMENT_INTEIGENCE_ENDPOINT = var.env_variables.azure_document_inteligence_endpoint
      AZURE_KEY_CREDENTIAL               = var.env_variables.azure_key_credential
      AZURE_API_VERSION                  = var.env_variables.azure_api_version

      # SPREADSHEET関連
      SPREADSHEET_ID         = var.env_variables.spreadsheet_id
      EXPENDITURE_SHEET_NAME = var.env_variables.expenditure_sheet_name

      # AWS関連
      SQS_QUEUE_URL = var.analyse_receipt_queue.url
    }
  }
}

locals {
  lambda_arns = { for k, function in aws_lambda_function.lambda_functions : k => function.arn }
}

# https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_event_source_mapping
resource "aws_lambda_event_source_mapping" "default" {
  event_source_arn = var.analyse_receipt_queue.arn
  function_name    = local.lambda_arns["analyze_receipt_function"]
}

# https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function_url
resource "aws_lambda_function_url" "line_bot_handler_url" {
  function_name      = local.lambda_arns["line_bot_handler_function"]
  authorization_type = "NONE"
}

# https://developer.hashicorp.com/terraform/language/resources/terraform-data
resource "terraform_data" "set_webhook" {
  triggers_replace = [
    aws_lambda_function_url.line_bot_handler_url.function_url,
    filebase64("../../scripts/configure_line_bot.py"),
    filebase64("../../scripts/rich_menu.json"),
    filebase64("../../scripts/richmenu.png"),
  ]

  provisioner "local-exec" {
    command = "CHANNEL_ACCESS_TOKEN=${var.env_variables.channel_access_token} python ../../scripts/configure_line_bot.py ${aws_lambda_function_url.line_bot_handler_url.function_url}"

    on_failure = fail
  }
}
