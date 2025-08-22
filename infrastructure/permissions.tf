resource "azurerm_role_assignment" "purview_msi__dedicated_purview_storage" {
  scope = azurerm_storage_account.dedicated_purview_storage.id
  role_definition_name = "Storage Blob Data Reader"
  principal_id = azurerm_purview_account.management.identity.0.principal_id
}
