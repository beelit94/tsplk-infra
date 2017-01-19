


module "master" {
  source = "salt_master"
  atlas_version = "${var.atlas_version}"
  atlas_token = "${var.atlas_token}"
  aws_region = "${var.aws_region}"
  username = "${var.username}"
  project_name = "${var.project_name}"
  public_key_path = "${var.public_key_path}"
  tsplk_formula_version = "${var.tsplk_formula_version}"
  master_instance_type = "${var.master_instance_type}"
  aws_zone_id = "${var.aws_zone_id}"
  aws_security_group_ids = "${var.aws_security_group_ids}"
  tsplk_bucket_name = "${var.tsplk_bucket_name}"
}

module "minion" {
  source = "salt_minion"
  atlas_version = "${var.atlas_version}"
  atlas_token = "${var.atlas_token}"
  aws_region = "${var.aws_region}"
  username = "${var.username}"
  project_name = "${var.project_name}"
  public_key_path = "${var.public_key_path}"
  key_pair_name = "${module.master.key_pair_name}"
  master_record_name = "${module.master.master_record_name}"
  aws_zone_id = "${var.aws_zone_id}"
  aws_security_group_ids = "${var.aws_security_group_ids}"
  platforms = "${var.platforms}"
  volume_sizes = "${var.volume_sizes}"
  instance_types = "${var.instance_types}"
  rdp_password = "${var.rdp_password}"
  user_data_map = "${var.user_data_map}"
}