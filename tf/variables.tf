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
  type = "map"
  default = {}
}
// number of minion id as key, volume_size as value.
variable "volume_sizes" {
  type = "map"
  default = {}
}
// number of minion id as key, instance_type as value.
variable "instance_types" {
  type = "map"
  default = {}
}

// aws info ===================================
// global info
variable "access_key" {}
variable "secret_key" {}
variable "aws_zone_id" {}
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
    "ubuntu-1404" = "linux",
    "windows-2008-r2" = "windows",
    "windows-2012-r2" = "windows",
  }
}
variable "tsplk_bucket_name" {
  default = "tsplk-bucket"
}

