variable "username" {}
variable "aws_region" {}

provider "aws" {
  region = "${var.aws_region}"
}

resource "aws_s3_bucket" "user_bucket" {
  bucket = "tsplk-${var.username}"
  region = "${var.aws_region}"
}