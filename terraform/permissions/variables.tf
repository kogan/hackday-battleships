
variable "project" {
  type        = string
  description = "The Google Cloud Platform project name"
}

variable "service" {
  type        = string
  default     = "battleships-app"
  description = "Name of the service"
}

variable "region" {
  type    = string
  default = "asia-northeast1"
}


variable "database_url" {
  type        = string
  description = "The ODBC connection string"
}

variable "superuser" {
  type        = string
  description = "The Django admin user account to create"
  default     = "admin"
}

