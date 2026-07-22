variable "environment" {
  description = "The name of the environment in which resources will be deployed"
  type        = string
}

variable "system_asset_owner" {
  description = "tagging - value extracted from ADO library secret"
  type        = string
  sensitive   = true
}
