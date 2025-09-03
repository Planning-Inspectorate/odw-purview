# resource "azurerm_virtual_network" "purview_resources_vnet" {
#   name                = "vnet-pview"
#   location            = local.location
#   resource_group_name = azurerm_resource_group.data_management.name
#   address_space       = [local.vnet_base_cidr_block]

#   tags = local.tags
# }

# resource "azurerm_subnet" "purview_resources_subnet" {
#   name                 = "vnet-pview-subnet"
#   resource_group_name  = azurerm_resource_group.data_management.name
#   virtual_network_name = azurerm_virtual_network.purview_resources_vnet.name
#   address_prefixes     = [local.vnet_subnet_ip_range]

#   service_endpoints = ["Microsoft.Storage"]
# }

# resource "azurerm_network_security_group" "nsg" {
#   name                = "pins-nsg-apim-pview-${var.environment}"
#   location            = local.location
#   resource_group_name = azurerm_resource_group.data_management.name

#   tags = local.tags
# }

# resource "azurerm_subnet_network_security_group_association" "nsg" {
#   network_security_group_id = azurerm_network_security_group.nsg.id
#   subnet_id                 = azurerm_subnet.purview_resources_subnet.id

#   depends_on = [
#     azurerm_network_security_group.nsg
#   ]
# }

# resource "azurerm_private_dns_zone_virtual_network_link" "purview_resources_vnet_link" {
#   for_each              = toset([for dns_zone in azurerm_private_dns_zone.data_lake_dns_zone : dns_zone.name])
#   name                  = "dfs-vnet-pview"
#   resource_group_name   = azurerm_resource_group.data_management.name
#   private_dns_zone_name = each.key
#   virtual_network_id    = azurerm_virtual_network.purview_resources_vnet.id

#   tags = local.tags
# }

# resource "azurerm_private_dns_zone_virtual_network_link" "purview_vnet_link" {
#   name                  = "dfs-vnet-pview-platform"
#   resource_group_name   = azurerm_resource_group.data_management.name
#   private_dns_zone_name = azurerm_private_dns_zone.purview_platform_dns_zone.name
#   virtual_network_id    = azurerm_virtual_network.purview_resources_vnet.id

#   tags = local.tags
# }

# resource "azurerm_private_dns_zone_virtual_network_link" "purview_account_vnet_link" {
#   name                  = "dfs-vnet-pview-account"
#   resource_group_name   = azurerm_resource_group.data_management.name
#   private_dns_zone_name = azurerm_private_dns_zone.purview_dns_zone.name
#   virtual_network_id    = azurerm_virtual_network.purview_resources_vnet.id

#   tags = local.tags
# }

# resource "azurerm_private_dns_zone_virtual_network_link" "purview_servicebus_vnet_link" {
#   name                  = "dfs-vnet-pview-servicebus"
#   resource_group_name   = azurerm_resource_group.data_management.name
#   private_dns_zone_name = azurerm_private_dns_zone.service_bus_dns_zone.name
#   virtual_network_id    = azurerm_virtual_network.purview_resources_vnet.id

#   tags = local.tags
# }


# # Tooling vnet resources
# data "azurerm_virtual_network" "tooling" {
#   name                = local.tooling_config.network_name
#   resource_group_name = local.tooling_config.network_rg

#   provider = azurerm.tooling
# }

# resource "azurerm_virtual_network_peering" "purview_to_tooling" {
#   name                      = "pins-peer-pview-to-tooling-${var.environment}"
#   resource_group_name       = azurerm_resource_group.data_management.name
#   virtual_network_name      = azurerm_virtual_network.purview_resources_vnet.name
#   remote_virtual_network_id = data.azurerm_virtual_network.tooling.id
# }

# resource "azurerm_virtual_network_peering" "tooling_to_purview" {
#   name                      = "pins-peer-tooling-to-pview-${var.environment}"
#   resource_group_name       = local.tooling_config.network_rg
#   virtual_network_name      = local.tooling_config.network_name
#   remote_virtual_network_id = azurerm_virtual_network.purview_resources_vnet.id

#   provider = azurerm.tooling
# }

# # DNS zones
# resource "azurerm_private_dns_zone" "data_lake_dns_zone" {
#   for_each            = toset(["dfs", "blob", "queue"])
#   name                = "privatelink.${each.key}.core.windows.net"
#   resource_group_name = azurerm_resource_group.data_management.name

#   tags = local.tags
# }

# resource "azurerm_private_dns_zone" "purview_dns_zone" {
#   # Purview account
#   name                = "privatelink.purview.azure.com"
#   resource_group_name = azurerm_resource_group.data_management.name

#   tags = local.tags
# }

# resource "azurerm_private_dns_zone" "purview_platform_dns_zone" {
#   # Purview platform
#   name                = "privatelink.purview-service.microsoft.com"
#   resource_group_name = azurerm_resource_group.data_management.name

#   tags = local.tags
# }

# resource "azurerm_private_dns_zone" "service_bus_dns_zone" {
#   name                = "privatelink.servicebus.windows.net"
#   resource_group_name = azurerm_resource_group.data_management.name

#   tags = local.tags
# }

# data "azurerm_private_dns_zone" "tooling_storage" {
#   for_each = toset(local.storage_zones)

#   name                = "privatelink.${each.key}.core.windows.net"
#   resource_group_name = local.tooling_config.network_rg

#   provider = azurerm.tooling
# }

# resource "azurerm_private_endpoint" "purview_platform_private_endpoint" {
#   name                = "pins-pe-platform${azurerm_purview_account.management.name}"
#   resource_group_name = azurerm_resource_group.data_management.name
#   location            = local.location
#   subnet_id           = azurerm_subnet.purview_resources_subnet.id

#   private_dns_zone_group {
#     name = "purviewDnsZone"
#     private_dns_zone_ids = concat(
#       [for dns_zone in azurerm_private_dns_zone.data_lake_dns_zone : dns_zone.id],
#       [azurerm_private_dns_zone.purview_dns_zone.id, azurerm_private_dns_zone.purview_platform_dns_zone.id]
#     )
#   }

#   private_service_connection {
#     name                           = "purviewDfs"
#     is_manual_connection           = false
#     private_connection_resource_id = azurerm_purview_account.management.id
#     subresource_names              = ["platform"]
#   }

#   tags = local.tags
# }

# resource "azurerm_private_endpoint" "data_lake" {
#   name                = "pins-pe-${azurerm_storage_account.dedicated_purview_storage.name}"
#   resource_group_name = azurerm_resource_group.data_management.name
#   location            = local.location
#   subnet_id           = azurerm_subnet.purview_resources_subnet.id

#   private_dns_zone_group {
#     name                 = "dataLakeDnsZone"
#     private_dns_zone_ids = [for dns_zone in azurerm_private_dns_zone.data_lake_dns_zone : dns_zone.id]
#   }

#   private_service_connection {
#     name                           = "dataLakeDfs"
#     is_manual_connection           = false
#     private_connection_resource_id = azurerm_storage_account.dedicated_purview_storage.id
#     subresource_names              = ["dfs"]
#   }

#   tags = local.tags
# }

# # private endpoints in tooling

# resource "azurerm_private_endpoint" "tooling_data_lake" {
#   for_each = toset(local.storage_zones)

#   name                = "pins-pe-pview-${each.key}-tooling-pview-${var.environment}-uks"
#   resource_group_name = azurerm_resource_group.data_management.name
#   location            = local.location
#   subnet_id           = azurerm_subnet.purview_resources_subnet.id

#   private_dns_zone_group {
#     name                 = "storagePrivateDnsZone${each.key}"
#     private_dns_zone_ids = [data.azurerm_private_dns_zone.tooling_storage[each.key].id]
#   }

#   private_service_connection {
#     name                           = "storagePrivateServiceConnection${each.key}"
#     is_manual_connection           = false
#     private_connection_resource_id = azurerm_storage_account.dedicated_purview_storage.id
#     subresource_names              = [each.key]
#   }

#   tags = local.tags
# }


# # Purview managed private endpoints
# resource "azurerm_private_endpoint" "purview_ingestion_blob" {
#   name                = "pe-pins-pview-${var.environment}-ingestion-blob"
#   location            = local.location
#   resource_group_name = azurerm_resource_group.data_management.name
#   subnet_id           = azurerm_subnet.purview_resources_subnet.id

#   private_dns_zone_group {
#     name                 = "purviewBlobPrivateDnsZone"
#     private_dns_zone_ids = [azurerm_private_dns_zone.data_lake_dns_zone["blob"].id]
#   }
#   private_service_connection {
#     name                           = "purviewBlobServiceConnection"
#     private_connection_resource_id = azurerm_purview_account.management.managed_resources[0].storage_account_id
#     is_manual_connection           = false
#     subresource_names              = ["blob"]
#   }
# }

# resource "azurerm_private_endpoint" "purview_ingestion_queue" {
#   name                = "pe-pins-pview-${var.environment}-ingestion-queue"
#   location            = local.location
#   resource_group_name = azurerm_resource_group.data_management.name
#   subnet_id           = azurerm_subnet.purview_resources_subnet.id

#   private_dns_zone_group {
#     name                 = "purviewQueuePrivateDnsZone"
#     private_dns_zone_ids = [azurerm_private_dns_zone.data_lake_dns_zone["queue"].id]
#   }
#   private_service_connection {
#     name                           = "purviewQueueServiceConnection"
#     private_connection_resource_id = azurerm_purview_account.management.managed_resources[0].storage_account_id
#     is_manual_connection           = false
#     subresource_names              = ["queue"]
#   }
# }

# resource "azurerm_private_endpoint" "purview_ingestion_namespace" {
#   name                = "pe-pins-pview-${var.environment}-ingestion-namespace"
#   location            = local.location
#   resource_group_name = azurerm_resource_group.data_management.name
#   subnet_id           = azurerm_subnet.purview_resources_subnet.id

#   private_dns_zone_group {
#     name                 = "purviewNamespacePrivateDnsZone"
#     private_dns_zone_ids = [azurerm_private_dns_zone.service_bus_dns_zone.id]
#   }
#   private_service_connection {
#     name                           = "purviewNamespaceServiceConnection"
#     private_connection_resource_id = azurerm_purview_account.management.managed_resources[0].event_hub_namespace_id
#     is_manual_connection           = false
#     subresource_names              = ["namespace"]
#   }
# }
