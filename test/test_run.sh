#!/usr/bin/env bash
user=$(cat test/salt_master_var.json | jq -r .'username')
project=$(cat test/salt_master_var.json | jq -r .'project_name')
terraform remote config -backend=s3 -backend-config="bucket=tsplk-bucket" \
-backend-config="key=base/$user/$project/terraform.tfstate" \
-backend-config="region=us-west-2"
terraform apply -var-file=test/salt_master_var.json tf/salt_master