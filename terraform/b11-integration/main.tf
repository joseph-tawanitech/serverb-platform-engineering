terraform {
  required_version = ">= 1.16.0"
}

variable "environment" {
  description = "Environment passed from Terraform to Ansible"
  type        = string
  default     = "server-b"
}

resource "terraform_data" "serverb_handoff" {
  input = var.environment
}

output "environment" {
  value = terraform_data.serverb_handoff.output
}
