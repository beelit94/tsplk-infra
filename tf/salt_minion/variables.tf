//atlas info =============================
variable "atlas_version" {
  type = "map"
  default = {
    "ubuntu_1404" = "latest"
    "windows_2008_r2" = "latest"
    "windows_2012_r2" = "latest"
    "salt_master" = "latest"
  }
}
variable "atlas_token" {}


//tsplk global info =============================
variable "username" {}
variable "project_name" {}
// rdp password of windows vm
variable "rdp_password" {
  default = "win@ChangeThis"
}

// tsplk master info ===========================
variable "master_record_name" {}
variable "key_pair_name" {}

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
    "ubuntu_1404" = "linux",
    "windows_2008_r2" = "windows",
    "windows_2012_r2" = "windows",
  }
}

variable "atlas_artifact_map"{
  type = "map"
  default = {
    "ubuntu_1404" = "splunk-sus-qa/ubuntu-1404",
    "windows_2008_r2" = "splunk-sus-qa/windows-2008-r2",
    "windows_2012_r2" = "splunk-sus-qa/windows-2012-r2"
  }
}
