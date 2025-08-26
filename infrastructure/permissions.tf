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
