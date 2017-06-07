# Naming convention
# 1. all name should be splitted by underline instead of dash
# 2. default shouldn't be given for testability and debuggablity unlesss it's map

//atlas info =============================
variable "atlas_version" {
  type = "map"

  default = {
    "ubuntu_1404"     = "latest"
    "windows_2008_r2" = "latest"
    "windows_2012_r2" = "latest"
    "salt_master"     = "latest"
  }
}

variable "atlas_token" {}

//tsplk global info =============================
variable "username" {}

variable "project_name" {}

// relative path of working folder
variable "public_key_path" {}

// rdp password of windows vm
variable "rdp_password" {
  default = "win@ChangeThis"
}

variable "tsplk_formula_version" {
  default = "master"
}

// tsplk master info ===========================
variable "master_instance_type" {}

variable "master_files" {
  type = "map"
}

variable "master_file_names" {
  type = "map"
}

// tpslk minion info ===========================
// number of minion id as key, platform as value.
variable "platforms" {
  type    = "map"
  default = {}
}

// number of minion id as key, volume_size as value.
variable "volume_sizes" {
  type    = "map"
  default = {}
}

// number of minion id as key, instance_type as value.
variable "instance_types" {
  type    = "map"
  default = {}
}

// aws info ===================================
variable "aws_zone_name" {}

variable "aws_region" {
  default = "us-west-2"
}

// region specific, list of map
variable "aws_security_group_ids" {
  type = "map"
}

// maping user data with platform
variable "user_data_map" {
  type = "map"

  default = {
    "ubuntu_1404"     = "linux"
    "windows_2008_r2" = "windows"
    "windows_2012_r2" = "windows"
  }
}

variable "tsplk_bucket_name" {
  default = "tsplk-bucket"
}
