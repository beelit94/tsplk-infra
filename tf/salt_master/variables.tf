//atlas info =============================
variable "atlas_version" {
  type = "map"
  default = {
    "ubuntu-1404" = "latest"
    "windows-2008-r2" = "latest"
    "windows-2012-r2" = "latest"
    "salt-master" = "latest"
  }
}
variable "atlas_token" {}


//tsplk global info =============================
variable "username" {}
variable "project_name" {}
// relative path of working folder
variable "public_key_path" {}

variable "tsplk_formula_version" {
  default = "master"
}

// tsplk master info ===========================
variable "master_instance_type" {}
variable "master_file_names" {
  type = "map"
}
variable "master_files" {
  type = "map"
}

// aws info ===================================
// global info
variable "aws_zone_name" {}
variable "aws_region" {
  default = "us-west-2"
}
// region specific, list of map
variable "aws_security_group_ids" {
  type = "map"
}

variable "tsplk_bucket_name" {
  default = "tsplk-bucket"
}

