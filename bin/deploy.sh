#!/bin/bash
LAMBDA_CODE_BUCKET=$(aws ssm get-parameter --region us-west-2 --name LAMBDA_CODE_BUCKET | jq -r '.Parameter.Value')
echo $LAMBDA_CODE_BUCKET

aws cloudformation package \
--template-file resources/sam.yaml \
--region us-west-2
--output-template-file resources/cf.yaml \
--s3-bucket $LAMBDA_CODE_BUCKET --s3-prefix LUAU

aws cloudformation deploy \
--region us-west-2 \
--template-file resources/cf.yaml \
--stack-name LUAU_Tagger \
--capabilities CAPABILITY_IAM