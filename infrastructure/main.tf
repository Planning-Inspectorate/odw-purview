resource "azurerm_resource_group" "data_management" {
  name     = "pins-rg-datamgmt"
  location = module.azure_region.location_cli

  tags = local.tags
}

resource "azurerm_purview_account" "management" {
  name                        = "pins-pview"
  resource_group_name         = azurerm_resource_group.data_management.name
  location                    = local.location
  managed_resource_group_name = "${azurerm_resource_group.data_management.name}-purview-managed"

  identity {
    type = "SystemAssigned"
  }

  tags = local.tags
}


resource "azurerm_storage_account" "dedicated_purview_storage" {
  name                             = "pinsstpview"
  resource_group_name              = azurerm_resource_group.data_management.name
  location                         = local.location
  account_tier                     = "Standard"
  account_replication_type         = "LRS"
  account_kind                     = "StorageV2"
  default_to_oauth_authentication  = true
  https_traffic_only_enabled       = true
  is_hns_enabled                   = true
  min_tls_version                  = "TLS1_2"
  public_network_access_enabled    = true
  cross_tenant_replication_enabled = true
  tags                             = local.tags
}

resource "azurerm_storage_data_lake_gen2_filesystem" "self_serve_analytics_data_lake" {
  name               = "selfServeAnalytics"
  storage_account_id = azurerm_storage_account.dedicated_purview_storage.id
}
