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
variable "master_files" {
  // data file paths to sync to tsplk master,
  // which sould be relative to working folder(project folder in tsplk)
  type = "map"
  default = {}
}

variable "master_file_names" {
  // same as master_files, pass only name here
  // todo json terraform dict problem
  type = "map"
  default = {}
}

// aws info ===================================
// global info
variable "aws_zone_id" {}
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

output "master_record_name"{
  value = "${aws_route53_record.salt-master-record.name}"
}

output "key_pair_name"{
  value = "${aws_key_pair.key.key_name}"
}