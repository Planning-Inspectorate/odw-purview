locals {
  service_name = "odw"
  location     = "uk-south"
  tags = {
    CreatedBy   = "Terraform"
    Environment = var.environment
    ServiceName = local.service_name
  }
}