provider "aws" {
  region = "${var.aws_region}"
}

resource "aws_key_pair" "key" {
  key_name = "tsplk-${var.username}-${var.project_name}"
  public_key = "${file("${path.cwd}/${var.public_key_path}")}"
}

data "template_file" "master-user-data" {
  template = "${file("${path.module}/user_data/master")}"
  vars {
    user = "${var.username}"
    project = "${var.project_name}"
    bucket_name = "${var.tsplk_bucket_name}"
  }
}

data "aws_route53_zone" "tsplk_zone" {
  name = "${var.aws_zone_name}"
}

resource "aws_instance" "salt_master" {
  ami = "${var.amis["salt_master"]}"
  instance_type = "${var.master_instance_type}"
  vpc_security_group_ids = "${var.aws_security_group_ids[var.aws_region]}"
  tags {
    Name = "${var.username}-${var.project_name}-saltmaster"
    User = "${var.username}"
    Project = "${var.project_name}"
  }

  key_name = "${aws_key_pair.key.key_name}"

  ebs_block_device {
    device_name = "/dev/sda1"
    volume_size = "50"
  }

  user_data = "${data.template_file.master-user-data.rendered}"
  iam_instance_profile = "tsplk"

  depends_on = ["aws_s3_bucket_object.pillar_data"]

}

resource "aws_eip" "salt-master-eip" {
  vpc = true
  instance = "${aws_instance.salt_master.id}"
}

resource "aws_route53_record" "salt-master-record" {
  // same number of records as instances
  zone_id = "${data.aws_route53_zone.tsplk_zone.zone_id}"
  // todo, beaware we hard code saltmaster name here
  name = "${var.username}-${var.project_name}-saltmaster"
  type = "CNAME"
  ttl = "300"
  // matches up record N to instance N
//  todo due to bug https://github.com/hashicorp/terraform/issues/3216
  records = ["ec2-${replace("${aws_eip.salt-master-eip.public_ip}", ".", "-")}.${var.aws_region}.compute.amazonaws.com"]
}

resource "aws_s3_bucket_object" "pillar_data" {
  count = "${length(keys(var.master_files))}"
//  todo this is hard code by using simple bucket to create the bucket we needed
  bucket = "${var.tsplk_bucket_name}"
  key = "${var.username}-${var.project_name}/${lookup(var.master_file_names, count.index)}"
  source = "${path.cwd}/${lookup(var.master_files, count.index)}"
  etag = "${md5(file("${path.cwd}/${lookup(var.master_files, count.index)}"))}"
}