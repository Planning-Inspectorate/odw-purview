terraform {
  backend "azurerm" {
    # Per-environment key specified in ./environments/*.tfbackend
    container_name       = "terraformstate-purview-prod"
    resource_group_name  = "pins-rg-shared-terraform-uks"
    subscription_id      = "edb1ff78-90da-4901-a497-7e79f966f8e2"
    storage_account_name = "pinsstsharedtfstateuks"
  }

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "= 4.28.0"
    }
  }
  required_version = ">= 1.11.0, < 1.13.0"
}

provider "azurerm" {
  resource_provider_registrations = "none"
  features {}
}

provider "azurerm" {
  subscription_id                 = var.tooling_config.subscription_id
  alias                           = "tooling"
  resource_provider_registrations = "none"

  features {}
}
