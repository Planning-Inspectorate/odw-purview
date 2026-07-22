locals {
  service_name             = "odw" # Temporary for now
  location                 = "uksouth"
  data_lake_retention_days = 28
  #vnet_base_cidr_block     = "10.111.0.0/24"
  #vnet_subnet_ip_range     = "10.111.0.0/25"
  #storage_zones = ["blob", "dfs", "file", "queue", "table", "web"]  # Commented out because the networking currently cannot be used
  dedicated_purview_storage_role_assignments = [
    {
      role_definition_name = "Storage Blob Data Contributor"
      principal_id         = "0cad1989-27de-4242-a06b-7cad373497e7" # Azure DevOps Pipelines - ODW Prod - Infrastructure"
    }
  ]

  tags = merge(
    {
      CreatedBy   = "Terraform"
      Environment = var.environment
      ServiceName = local.service_name
    },
    var.environment == "prod" ? {
      SystemAssetOwner    = var.system_asset_owner
      BusinessProcess     = "ODW"
      PersonalData        = "No"
      SpecialCategoryData = "No"
      ProtectiveMarking   = "Official-Sensitive-Mission-Critical"
      CriticalityRating   = "Level 2"
    } : {}
  )
}
