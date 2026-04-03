provider "aws" {
  region = "eu-central-1"
}

locals {
  prefix = "stefanyshyn-pavlo-17"
}

# SNS (ДОДАНО)
resource "aws_sns_topic" "alerts" {
  name = "${local.prefix}-alerts"
}

# Email subscription
resource "aws_sns_topic_subscription" "email" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = "stefanyshynpavlo@gmail.com"
}

# DynamoDB
module "database" {
  source     = "../../modules/dynamodb"
  table_name = "thresholds"
}

# Lambda
module "backend" {
  source              = "../../modules/lambda"
  function_name       = "${local.prefix}-api-handler"
  source_file         = "${path.root}/../../src/app.py"
  dynamodb_table_arn  = module.database.table_arn
  dynamodb_table_name = module.database.table_name
  sns_topic_arn       = aws_sns_topic.alerts.arn
  s3_bucket_name      = aws_s3_bucket.alerts_audio.bucket
}

# API Gateway
module "api" {
  source               = "../../modules/api_gateway"
  api_name             = "${local.prefix}-http-api"
  lambda_invoke_arn    = module.backend.invoke_arn
  lambda_function_name = module.backend.function_name
}

output "api_url" {
  value = module.api.api_endpoint
}

resource "random_id" "suffix" {
  byte_length = 4
}

resource "aws_s3_bucket" "alerts_audio" {
  bucket        = "${local.prefix}-alerts-audio-${random_id.suffix.hex}"
  force_destroy = true
}

output "s3_bucket_name" {
  value = aws_s3_bucket.alerts_audio.bucket
}