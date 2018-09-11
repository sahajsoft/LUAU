#!/bin/bash
LAMBDA_CODE_BUCKET=$(aws ssm get-parameter --region us-west-2 --name LAMBDA_CODE_BUCKET | jq -r '.Parameter.Value')
echo $LAMBDA_CODE_BUCKET

source resources/env.properties

aws cloudformation package \
--template-file resources/sam.yaml \
--region $AWS_REGION \
--output-template-file resources/cf.yaml \
--s3-bucket $LAMBDA_CODE_BUCKET --s3-prefix LUAU

aws cloudformation deploy \
--region $AWS_REGION \
--parameter-overrides AWS_REGION=$AWS_REGION SES_EMAIL=$SES_EMAIL ADMIN_EMAIL=$ADMIN_EMAIL \
--template-file resources/cf.yaml \
--stack-name LUAUTagger \
--capabilities CAPABILITY_IAM