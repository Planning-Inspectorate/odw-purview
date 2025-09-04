variable "environment" {
  description = "The name of the environment in which resources will be deployed"
  type        = string
}

variable "ado_agent_sp_ids" {
  description = "The ids of the Service Principals that are used for ADO pipelines"
  type        = string
  default     = ""
}
