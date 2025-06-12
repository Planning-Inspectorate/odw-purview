locals {
  service_name = "odw" # Temporary for now
  location     = "uksouth"
  tags = {
    CreatedBy   = "Terraform"
    Environment = var.environment
    ServiceName = local.service_name
  }
}