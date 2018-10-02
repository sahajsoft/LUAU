#!/bin/bash
LAMBDA_CODE_BUCKET=$(aws ssm get-parameter --region us-west-2 --name LAMBDA_CODE_BUCKET | jq -r '.Parameter.Value')
SES_EMAIL=$(aws ssm get-parameter --region us-west-2 --name SES_EMAIL | jq -r '.Parameter.Value')
ADMIN_EMAIL=$(aws ssm get-parameter --region us-west-2 --name ADMIN_EMAIL | jq -r '.Parameter.Value')
echo $LAMBDA_CODE_BUCKET
echo $SES_EMAIL
echo $ADMIN_EMAIl
source resources/env.properties

aws cloudformation package \
--template-file resources/sam.yaml \
--region $AWS_REGION \
--output-template-file resources/cf.yaml \
--s3-bucket $LAMBDA_CODE_BUCKET --s3-prefix LUAU

aws cloudformation deploy \
--region $AWS_REGION \
--parameter-overrides SESEMAIL=$SES_EMAIL ADMINEMAIL=$ADMIN_EMAIL \
--template-file resources/cf.yaml \
--stack-name LUAUTagger \
--capabilities CAPABILITY_IAM