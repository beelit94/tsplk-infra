variable "aws_access_key" {}
variable "aws_secret_key" {}
variable "username" {}
variable "project_name" {}

variable "atlas_token" {
  # todo, store this token at somewhere else
  default = "zzRR9ziEHspkqg.atlasv1.UM4GyPYRHGeDyqFu536Bl5nuRGTdPuN5T0BorWu1cZeGUdZx90ZgD0qWFltFDlzEB0E"
}
variable "key_name" {
  default = "id_rsa"
}
variable "master_instance_type" {
  default = "m3.large"
}
variable "ubuntu-salt-master-version" {
  default = "latest"
}

provider "atlas" {
  # You can also set the atlas token by exporting
  # ATLAS_TOKEN into your env
  token = "${var.atlas_token}"
}

provider "aws" {
    access_key = "${var.aws_access_key}"
    secret_key = "${var.aws_secret_key}"
    region = "us-west-2"
}

# atlas
resource "atlas_artifact" "ubuntu-salt-master" {
  name = "splunk-sus-qa/ubuntu-1404-saltmaster"
  type = "amazon.ami"
  version = "${var.ubuntu-salt-master-version}"
}

resource "aws_key_pair" "key" {
  key_name = "tsplk-${var.username}-${var.project_name}"
  public_key = "${file("${var.key_name}.pub")}"
}

resource "aws_instance" "ubuntu-salt-master" {
  ami = "${atlas_artifact.ubuntu-salt-master.metadata_full.ami_id}"
  instance_type = "${var.master_instance_type}"
  security_groups = ["terraform-salty-splunk"]
  tags {
    Name = "${var.username}-${var.project_name}-ubuntu-1404-saltmaster"
    User = "${var.username}"
    Project = "${var.project_name}"
  }
  # count = "${var.ubuntu_saltmaster_count}"
  key_name = "${aws_key_pair.key.key_name}"
  
  connection {
      type = "ssh"
      user = "ubuntu"
      private_key = "${file("${var.key_name}")}"
      timeout = "10m"
  }

  ebs_block_device {
    device_name = "/dev/sda1"
    volume_size = "50"
  }

  # packer should create this folder already
  provisioner "file" {
    source = "sync_to_file_base"
    destination = "."
  }

  provisioner "file" {
    source = "settings.yml"
    destination = "settings.yml"
  }

}

output "salt-master-public-ip" {
    value = "${aws_instance.ubuntu-salt-master.public_ip}"
}

output "salt-master-private-ip" {
    value = "${aws_instance.ubuntu-salt-master.private_ip}"
}