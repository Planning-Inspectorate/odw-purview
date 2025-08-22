locals {
  service_name             = "odw" # Temporary for now
  location                 = "uksouth"
  data_lake_retention_days = 28
  vnet_base_cidr_block     = "10.110.0.0/24"
  vnet_subnet_ip_range     = "10.110.0.0/25"
  tooling_config = {
    network_name    = "pins-vnet-shared-tooling-uks"
    network_rg      = "pins-rg-shared-tooling-uks"
    subscription_id = "edb1ff78-90da-4901-a497-7e79f966f8e2"
  }
  tags = {
    CreatedBy   = "Terraform"
    Environment = var.environment
    ServiceName = local.service_name
  }
}