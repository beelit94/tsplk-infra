#!/usr/bin/env bash
user=$(cat test/salt_master_var.json | jq -r .'username')
project=$(cat ../test/data/salt_master_var.json | jq -r .'project_name')
aws_region=$(cat ../test/data/salt_master_var.json | jq -r .'aws_region')

terraform apply -var="username=$user" -var="aws_region=$aws_region" tf/simple_bucket

mkdir -p tmp/salt_master
cp -r tf/salt_master/* tmp/salt_master
cd tmp/salt_master

terraform remote config -backend=s3 -backend-config="bucket=tsplk-bucket" \
-backend-config="key=$user-$project/salt_master.tfstate" \
-backend-config="region=$aws_region"
terraform apply -var-file=../../test/salt_master_var.json

cd ../..