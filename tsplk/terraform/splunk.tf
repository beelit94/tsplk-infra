variable "aws_access_key" {}
variable "aws_secret_key" {}
variable "atlas_token" {}
variable "key_name" {}
variable "key_path" {}
variable "rdp_password" {}

variable "windows_2012_r2_count" {
  default = "0"
}
variable "windows_2008_r2_count" {
  default = "0"
}
variable "ubuntu_1404_count" {
  default = "0"
}

variable "ubuntu_saltmaster_count" {
  default = "0"
}

variable "salt_master_ip" {
  default = "None"
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

resource "aws_instance" "windows-2012-r2" {
  ami = "${atlas_artifact.windows-2012-r2.metadata_full.ami_id}"
  instance_type = "m4.large"
  security_groups = ["terraform-salty-splunk"]
  # depends_on = "aws_instance.salt-master"
  count = "${var.windows_2012_r2_count}"
  tags {
    Name = "${var.username}-${var.project_name}-windows-2012-r2-${count.index}"
  }

  connection {
    type = "winrm"
    user = "Administrator"
    password = "${var.rdp_password}"
    timeout = "10m"
  }

  provisioner "local-exec" {
    command = "sleep 300"
  }

  provisioner "remote-exec" {
    inline = [
      # splunk forwarder
      "\"C:\\Program Files\\SplunkUniversalForwarder\\bin\\splunk.exe\" add forward-server ${var.salt_master_ip}:9997 -auth admin:changeme",
      "\"C:\\Program Files\\SplunkUniversalForwarder\\bin\\splunk.exe\" set servername ${self.tags.Name}",
      "\"C:\\Program Files\\SplunkUniversalForwarder\\bin\\splunk.exe\" set default-hostname ${self.tags.Name}",
      "\"C:\\Program Files\\SplunkUniversalForwarder\\bin\\splunk.exe\" restart",
      # config minion
      # todo fix bug python not in the path
      "C:\\tools\\python2\\python C:\\update_minion_conf.py --kv master=${var.salt_master_ip} --kv id=${self.tags.Name}"
    ]
  }

  provisioner "local-exec" {
    command = "sleep 60"
  }
}

resource "aws_instance" "windows-2008-r2" {
  ami = "${atlas_artifact.windows-2008-r2.metadata_full.ami_id}"
  instance_type = "m4.large"
  security_groups = ["terraform-salty-splunk"]
  count = "${var.windows_2008_r2_count}"
  tags {
    Name = "${var.username}-${var.project_name}-windows-2008-r2-${count.index}"
  }

  connection {
    type = "winrm"
    user = "Administrator"
    password = "${var.rdp_password}"
    timeout = "10m"
  }

  provisioner "local-exec" {
    command = "sleep 300"
  }

  provisioner "remote-exec" {
    inline = [
      # splunk forwarder
      "\"C:\\Program Files\\SplunkUniversalForwarder\\bin\\splunk.exe\" add forward-server ${var.salt_master_ip}:9997 -auth admin:changeme",
      "\"C:\\Program Files\\SplunkUniversalForwarder\\bin\\splunk.exe\" set servername ${self.tags.Name}",
      "\"C:\\Program Files\\SplunkUniversalForwarder\\bin\\splunk.exe\" set default-hostname ${self.tags.Name}",
      "\"C:\\Program Files\\SplunkUniversalForwarder\\bin\\splunk.exe\" restart",
      # config minion
      # todo fix bug python not in the path
      "C:\\tools\\python2\\python C:\\update_minion_conf.py --kv master=${var.salt_master_ip} --kv id=${self.tags.Name}"
    ]
  }

  # wait for minion connect to master
  provisioner "local-exec" {
    command = "sleep 60"
  }
}

resource "aws_instance" "ubuntu-1404" {
  ami = "${atlas_artifact.ubuntu-1404.metadata_full.ami_id}"
  instance_type = "m4.large"
  security_groups = ["terraform-salty-splunk"]
  count = "${var.ubuntu_1404_count}"
  tags {
    Name = "${var.username}-${var.project_name}-ubuntu-1404-${count.index}"
  }
  key_name = "${var.key_name}"
  connection {
      type = "ssh"
      user = "ubuntu"
      key_file = "${var.key_path}"
      timeout = "10m"
  }

  provisioner "remote-exec" {
    inline = [
      # splunk forwarder
      "sudo /opt/splunkforwarder/bin/splunk add forward-server ${var.salt_master_ip}:9997 -auth admin:changeme",
      "sudo /opt/splunkforwarder/bin/splunk set servername ${self.tags.Name} -auth admin:changeme",
      "sudo /opt/splunkforwarder/bin/splunk set default-hostname ${self.tags.Name} -auth admin:changeme",
      "sudo /opt/splunkforwarder/bin/splunk restart",
      # config minion
      "sudo python update_minion_conf.py --kv master=${var.salt_master_ip} --kv id=${self.tags.Name}"
    ]
  }
}

resource "aws_instance" "ubuntu-salt-master" {
  ami = "${atlas_artifact.ubuntu-salt-master.metadata_full.ami_id}"
  instance_type = "m4.large"
  security_groups = ["terraform-salty-splunk"]
  tags {
    Name = "${var.username}-${var.project_name}-ubuntu-1404-saltmaster"
  }
  count = "${var.ubuntu_saltmaster_count}"
  key_name = "${var.key_name}"
  connection {
      type = "ssh"
      user = "ubuntu"
      key_file = "${var.key_path}"
      timeout = "10m"
  }

  ebs_block_device {
    device_name = "/dev/sda1"
    volume_size = "50"
  }


  provisioner "file" {
    source = "."
    destination = "."
  }

  provisioner "file" {
    source = "${var.key_path}"
    destination = "${var.key_name}"
  }


  provisioner "remote-exec" {
    inline = [
      "sudo /opt/splunk/bin/splunk set default-hostname salt-master -auth admin:changeme",
      "nohup sudo /opt/splunk/bin/splunk restart > splunk_start.log 2>&1 &",
      "sudo cp -r salt/file_base /srv/salt",
      "sudo cp -r salt/pillar /srv/pillar",
      # cp config
      "sudo cp salt/config/master /etc/salt/master",
      "sudo service salt-master restart"
    ]
  }
}

output "salt-master-public-ip" {
    value = "${aws_instance.ubuntu-salt-master.public_ip}"
}

output "salt-master-private-ip" {
    value = "${aws_instance.ubuntu-salt-master.private_ip}"
}