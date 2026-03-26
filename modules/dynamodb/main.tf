variable "table_name" {
  description = "The unique name of the DynamoDB table"
  type        = string
}

resource "aws_dynamodb_table" "main" {
  name         = var.table_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"

  attribute {
    name = "id"
    type = "S"
  }

  tags = {
    Project = "Threshold Alerts"
  }
}

resource "aws_dynamodb_table_item" "threshold_item" {
  table_name = aws_dynamodb_table.main.name
  hash_key   = "id"

  item = jsonencode({
    id        = { S = "main" }
    threshold = { N = "70" }
  })
}

output "table_name" {
  value = aws_dynamodb_table.main.name
}

output "table_arn" {
  value = aws_dynamodb_table.main.arn
}