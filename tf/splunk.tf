provider "atlas" {
  # You can also set the atlas token by exporting
  # ATLAS_TOKEN into your env
  token = "${var.atlas_token}"
}

provider "aws" {
    access_key = "${var.access_key}"
    secret_key = "${var.secret_key}"
    region = "${var.aws_region}"
}

data "aws_route53_zone" "tsplk-zone" {
  zone_id = "${var.aws_zone_id}"
}

data "atlas_artifact" "tsplk-artifact" {
  name = "splunk-sus-qa/${lookup(var.platforms, count.index)}"
  type = "amazon.ami"
  version = "${var.atlas_version["${lookup(var.platforms, count.index)}"]}"
  count = "${length(keys(var.platforms))}"
}

data "template_file" "user-data" {
  template = "${file("${path.cwd}/user_data/${lookup(var.user_data_map, lookup(var.platforms, count.index))}")}"
  count = "${length(keys(var.platforms))}"
  vars {
//    todo should use public dns instead
    salt_master_ip = "${aws_route53_record.salt-master-record.name}.${data.aws_route53_zone.tsplk-zone.name}"
    minion_id = "${var.username}-${var.project_name}-${count.index}"
    rdp_password = "${var.rdp_password}"
  }
}

resource "aws_instance" "splunk-instance" {
//  todo change this to region changable
  ami = "${element(data.atlas_artifact.tsplk-artifact.*.metadata_full.region-us-west-2, count.index)}"
  instance_type = "${lookup(var.instance_types, count.index)}"
  vpc_security_group_ids = "${var.aws_security_group_ids[var.aws_region]}"
  count = "${length(keys(var.platforms))}"
  tags {
    Name = "${var.username}-${var.project_name}-${count.index}"
    User = "${var.username}"
    Project = "${var.project_name}"
    Platform = "${lookup(var.platforms, count.index)}"
  }
  key_name = "${aws_key_pair.key.key_name}"

  root_block_device {
    volume_size = "${lookup(var.volume_sizes, count.index)}"
  }

  user_data = "${element(data.template_file.user-data.*.rendered, count.index)}"
}

resource "aws_eip" "eip" {
  vpc = true
  instance = "${element(aws_instance.splunk-instance.*.id, count.index)}"
  count = "${length(keys(var.platforms))}"
}

resource "aws_route53_record" "splunk-instance-record" {
  // same number of records as instances
  count = "${length(keys(var.platforms))}"
  zone_id = "${var.aws_zone_id}"
  name = "${var.username}-${var.project_name}-${count.index}"
  type = "CNAME"
  ttl = "300"
  // matches up record N to instance N
  // todo
  // due to bug https://github.com/hashicorp/terraform/issues/3216
  // should be directly refer to aws_instance public dns directly
  records = ["ec2-${replace("${element(aws_eip.eip.*.public_ip, count.index)}", ".", "-")}.${var.aws_region}.compute.amazonaws.com"]
}