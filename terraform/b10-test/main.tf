terraform {
  required_version = ">= 1.16.0"
}

variable "environment" {
  description = "Environment name for the B10 Terraform test"
  type        = string
  default     = "server-b"
}

output "environment" {
  value = var.environment
}
