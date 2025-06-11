locals {
  service_name = "odw"
  location     = "uksouth"
  tags = {
    CreatedBy   = "Terraform"
    Environment = var.environment
    ServiceName = local.service_name
  }
}