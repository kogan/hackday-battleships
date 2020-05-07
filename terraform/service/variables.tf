variable "project" {
  type        = string
  description = "The Google Cloud Platform project name"
}

variable "service" {
  description = "Name of the service"
  type        = string
  default     = "battleships-app"
}

variable "region" {
  default = "asia-northeast1"
  type    = string
}

variable "database_instance" {
  description = "Name of the postgres instance (PROJECT_ID:REGION:INSTANCE_NAME))"
  type        = string
}

variable "service_account_email" {
  description = "The identifying email address for the Cloud Run service account"
  type        = string
}
