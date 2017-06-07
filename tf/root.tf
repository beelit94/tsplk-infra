


module "master" {
  source = "./salt_master"
  atlas_version = "${var.atlas_version}"
  atlas_token = "${var.atlas_token}"
  aws_region = "${var.aws_region}"
  username = "${var.username}"
  project_name = "${var.project_name}"
  public_key_path = "${var.public_key_path}"
  tsplk_formula_version = "${var.tsplk_formula_version}"
  master_instance_type = "${var.master_instance_type}"
  aws_zone_name = "${var.aws_zone_name}"
  aws_security_group_ids = "${var.aws_security_group_ids}"
  tsplk_bucket_name = "${var.tsplk_bucket_name}"
  master_files = "${var.master_files}"
  master_file_names = "${var.master_file_names}"
}

module "minion" {
  source = "./salt_minion"
  atlas_version = "${var.atlas_version}"
  atlas_token = "${var.atlas_token}"
  aws_region = "${var.aws_region}"
  username = "${var.username}"
  project_name = "${var.project_name}"
  # todo if we specified module.master.aws_key_par_name here, on master require every varibles to be
  # same as local path, which is not ideal for now
  key_pair_name = "tsplk-${var.username}-${var.project_name}"
  # same here, ${module.master.master_record_name}
  master_record_name = "${var.username}-${var.project_name}-saltmaster.${var.aws_zone_name}"
  aws_zone_name = "${var.aws_zone_name}"
  aws_security_group_ids = "${var.aws_security_group_ids}"
  platforms = "${var.platforms}"
  volume_sizes = "${var.volume_sizes}"
  instance_types = "${var.instance_types}"
  rdp_password = "${var.rdp_password}"
  user_data_map = "${var.user_data_map}"
}

terraform {
  required_version = ">= 0.9.5"
  backend "s3" {
    bucket = "tsplk-bucket"
    region = "us-west-2"
  }
}