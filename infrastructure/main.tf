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
  #checkov:skip=CKV2_AZURE_40: Ensure storage account is not configured with Shared Key authorization (checkov v3)
  #checkov:skip=CKV2_AZURE_47: Ensure storage account is configured without blob anonymous access (checkov v3)
  #checkov:skip=CKV2_AZURE_41: Ensure storage account is configured with SAS expiration policy (checkov v3)
  #checkov:skip=CKV_AZURE_244: Avoid the use of local users for Azure Storage unless necessary (checkov v3)
  #checkov:skip=CKV_AZURE_35: Firewall is enabled using azurerm_storage_account_network_rules
  #checkov:skip=CKV_AZURE_59: Firewall is enabled using azurerm_storage_account_network_rules
  #checkov:skip=CKV_AZURE_190: Firewall is enabled using azurerm_storage_account_network_rules
  #checkov:skip=CKV_AZURE_206: Storage replication is defined in environment variables with ZRS default
  #checkov:skip=CKV2_AZURE_1: Microsoft managed keys are acceptable
  #checkov:skip=CKV2_AZURE_8: Firewall is enabled using azurerm_storage_account_network_rules
  #checkov:skip=CKV2_AZURE_18: Microsoft managed keys are acceptable
  #checkov:skip=CKV2_AZURE_33: Private Endpoint is not enabled as networking is controlled by Firewall
  #checkov:skip=CKV_AZURE_33: Queue service is not used by this storage account
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

  blob_properties {
    delete_retention_policy {
      days = local.data_lake_retention_days
    }

    container_delete_retention_policy {
      days = local.data_lake_retention_days
    }
  }

  network_rules {
    default_action             = "Allow"
    bypass                     = ["AzureServices"]
  }

  tags = local.tags
}

resource "azurerm_storage_data_lake_gen2_filesystem" "self_serve_analytics_data_lake" {
  name               = "self-serve-analytics"
  storage_account_id = azurerm_storage_account.dedicated_purview_storage.id
}
