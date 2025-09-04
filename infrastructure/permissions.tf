resource "azurerm_role_assignment" "purview_msi_dedicated_purview_storage" {
  scope                = azurerm_storage_account.dedicated_purview_storage.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_purview_account.management.identity[0].principal_id
}

resource "azurerm_role_assignment" "dedicated_purview_storage_permissions" {
  for_each = {
    for assignment in local.dedicated_purview_storage_role_assignments : "${assignment.role_definition_name}.${assignment.principal_id}" => assignment
  }
  scope                = azurerm_storage_account.dedicated_purview_storage.id
  role_definition_name = each.value.role_definition_name
  principal_id         = each.value.principal_id
}

# Purview admin permissions
data "azuread_group" "pins_purview_admins" {
  display_name = "pins-odw-purview-admins"
}

resource "azurerm_role_assignment" "purview_storage_data_owners" {
  scope                = azurerm_storage_account.dedicated_purview_storage.id
  role_definition_name = "Storage Blob Data Owner"
  principal_id         = data.azuread_group.pins_purview_admins.object_id
}

resource "azurerm_role_assignment" "ado_sp_purview_storage" {
  for_each             = toset(local.ado_agent_sp_ids)
  scope                = azurerm_storage_account.dedicated_purview_storage.id
  role_definition_name = "Role Based Access Control Administrator"
  principal_id         = each.key
}
