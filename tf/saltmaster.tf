data "atlas_artifact" "saltmaster" {
  name = "splunk-sus-qa/ubuntu-1404-saltmaster"
  type = "amazon.ami"
  version = "${var.atlas_version["salt-master"]}"
}

resource "aws_key_pair" "key" {
  key_name = "tsplk-${var.username}-${var.project_name}"
  public_key = "${file("${path.cwd}/${var.public_key_path}")}"
}

resource "aws_instance" "saltmaster" {
  ami = "${data.atlas_artifact.saltmaster.metadata_full.ami_id}"
  instance_type = "${var.master_instance_type}"
  vpc_security_group_ids = "${var.aws_security_group_ids[var.aws_region]}"
  tags {
    Name = "${var.username}-${var.project_name}-saltmaster"
    User = "${var.username}"
    Project = "${var.project_name}"
  }
  depends_on = ["aws_s3_bucket_object.pillar_data"]

  key_name = "${aws_key_pair.key.key_name}"

  ebs_block_device {
    device_name = "/dev/sda1"
    volume_size = "50"
  }

}

resource "aws_eip" "salt-master-eip" {
  vpc = true
  instance = "${aws_instance.saltmaster.id}"
}

resource "aws_route53_record" "salt-master-record" {
  // same number of records as instances
  zone_id = "${var.aws_zone_id}"
  name = "${var.username}-${var.project_name}-saltmaster"
  type = "CNAME"
  ttl = "300"
  // matches up record N to instance N
//  todo due to bug https://github.com/hashicorp/terraform/issues/3216
  records = ["ec2-${replace("${aws_eip.salt-master-eip.public_ip}", ".", "-")}.${var.aws_region}.compute.amazonaws.com"]
}

resource "aws_s3_bucket_object" "pillar_data" {
  count = "${length(keys(var.master_files))}"
  bucket = "${var.tsplk_bucket_name}"
  key = "${var.username}-${var.project_name}/${lookup(var.master_file_names, count.index)}"
  source = "${path.cwd}/${lookup(var.master_files, count.index)}"
  etag = "${md5(file("${lookup(var.master_files, count.index)}"))}"
}