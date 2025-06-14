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
