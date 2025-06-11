variable "environment" {
  description = "The name of the environment in which resources will be deployed"
  type        = string
}

variable "purview_admins" {
  description = "The administrators of the Purview account"
  type        = string
}
