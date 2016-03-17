variable "aws_access_key" {}
variable "aws_secret_key" {}
variable "atlas_token" {}
variable "key_name" {
  default = "id_rsa"
}
variable "username" {}
variable "project_name" {}

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
resource "atlas_artifact" "windows-2008-r2" {
  name = "splunk-sus-qa/windows-2008-r2"
  type = "amazon.ami"
  version = "latest"
}

resource "atlas_artifact" "windows-2012-r2" {
  name = "splunk-sus-qa/windows-2012-r2"
  type = "amazon.ami"
  version = "latest"
}

resource "atlas_artifact" "ubuntu-1404" {
  name = "splunk-sus-qa/ubuntu-1404"
  type = "amazon.ami"
  version = "latest"
}

resource "atlas_artifact" "ubuntu-salt-master" {
  name = "splunk-sus-qa/ubuntu-1404-saltmaster"
  type = "amazon.ami"
  version = "latest"
}

resource "aws_key_pair" "key" {
  key_name = "tsplk-${var.username}-${var.project_name}"
  public_key = "${file("${var.key_name}.pub")}"
}

resource "aws_instance" "ubuntu-salt-master" {
  ami = "ami-12fd1072"
  instance_type = "m3.large"
  security_groups = ["terraform-salty-splunk"]
  tags {
    Name = "${var.username}-${var.project_name}-ubuntu-1404-saltmaster"
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


  provisioner "remote-exec" {
    inline = [
      # call up the rest minion
      "nohup sudo -b xxx.py ${file("parameters")}"
    ]
  }
}

output "salt-master-public-ip" {
    value = "${aws_instance.ubuntu-salt-master.public_ip}"
}

output "salt-master-private-ip" {
    value = "${aws_instance.ubuntu-salt-master.private_ip}"
}