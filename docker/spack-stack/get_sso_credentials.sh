#!/usr/bin/env bash

profile=$1
aws configure export-credentials --format env --profile $profile > ./temporary_aws_credentials.sh
source ./temporary_aws_credentials.sh
rm -f ./temporary_aws_credentials.sh
cat mirrors.in.yaml | envsubst > mirrors.yaml
