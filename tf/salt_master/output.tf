output "master_record_name"{
  value = "${aws_route53_record.salt-master-record.name}.${data.aws_route53_zone.tsplk_zone.name}"
}

output "key_pair_name"{
  value = "${aws_key_pair.key.key_name}"
}