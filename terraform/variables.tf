variable "aws_access_key" {}
variable "aws_secret_key" {}

variable "aws_region" {
  default = "us-east-1"
}

variable "loader_role_path" {
  default = "/hbeers/"
}

variable "loader_role_name" {
  default = "hbeers_loader_role"
}

variable "loader_user_name" {
  default = "hbeers_loader_user"
}

variable "loader_s3_bucket_name" {
  default = "hbeers_loader"
}
