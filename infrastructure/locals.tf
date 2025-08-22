locals {
  service_name             = "odw" # Temporary for now
  location                 = "uksouth"
  data_lake_retention_days = 28
  tags = {
    CreatedBy   = "Terraform"
    Environment = var.environment
    ServiceName = local.service_name
  }
}