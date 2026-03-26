variable "function_name" { type = string }
variable "source_file" { type = string }
variable "dynamodb_table_arn" { type = string }
variable "dynamodb_table_name" { type = string }
variable "sns_topic_arn" { type = string }

# ZIP
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_file = var.source_file
  output_path = "${path.module}/app.zip"
}

# IAM роль
resource "aws_iam_role" "lambda_exec" {
  name = "${var.function_name}_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

# Логи
resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# DynamoDB (мінімальні права)
resource "aws_iam_role_policy_attachment" "lambda_dynamo_sns" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess"
}


# SNS доступ 
resource "aws_iam_role_policy_attachment" "lambda_sns" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSNSFullAccess"
}

# Lambda
resource "aws_lambda_function" "api_handler" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = var.function_name
  role             = aws_iam_role.lambda_exec.arn
  handler          = "app.handler"
  runtime          = "python3.12"
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  # Вимикаємо шифрування через KMS
  kms_key_arn = null

  environment {
    variables = {
      TABLE_NAME    = var.dynamodb_table_name
      SNS_TOPIC_ARN = var.sns_topic_arn
    }
  }
}

output "invoke_arn" {
  value = aws_lambda_function.api_handler.invoke_arn
}

output "function_name" {
  value = aws_lambda_function.api_handler.function_name
}

# Додаємо inline-політику для KMS (Decrypt)
resource "aws_iam_role_policy" "lambda_kms" {
  name = "${var.function_name}_kms_policy"
  role = aws_iam_role.lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "kms:Decrypt"
        Resource = "arn:aws:kms:eu-central-1:836822603043:key/38434272-ff01-4228-b750-fe890d6d1c2a"
      }
    ]
  })
}