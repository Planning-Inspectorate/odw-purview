locals {
  service_name             = "odw" # Temporary for now
  location                 = "uksouth"
  data_lake_retention_days = 28
  vnet_base_cidr_block     = "10.111.0.0/24"
  vnet_subnet_ip_range     = "10.111.0.0/25"
  tooling_config = {
    network_name    = "pins-vnet-shared-tooling-uks"
    network_rg      = "pins-rg-shared-tooling-uks"
    subscription_id = "edb1ff78-90da-4901-a497-7e79f966f8e2"
  }
  storage_zones = ["blob", "dfs", "file", "queue", "table", "web"]
  dedicated_purview_storage_role_assignments = [
    {
      role_definition_name = "Storage Blob Data Contributor"
      principal_id         = "0cad1989-27de-4242-a06b-7cad373497e7" # Azure DevOps Pipelines - ODW Prod - Infrastructure"
    }
  ]
  tags = {
    CreatedBy   = "Terraform"
    Environment = var.environment
    ServiceName = local.service_name
  }
}