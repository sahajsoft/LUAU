[![pipeline status](https://gitlab.com/keithw1/LUAU/badges/master/pipeline.svg)](https://gitlab.com/keithw1/LUAU/commits/master)

[![coverage report](https://gitlab.com/keithw1/LUAU/badges/master/coverage.svg)](https://gitlab.com/keithw1/LUAU/commits/master)

# Low Usage AWS Utility(LUAU)
LUAU is a plug-n-play suite of lambdas that aims to minimize the cost of operations of amazon account by acting upon Trusted Advisor(TA) recommendations.

### Documentation
You can read [the documentation here](https://keithw1.gitlab.io/LUAU/readme.html)


### Source Code
You can view [the source code here](https://gitlab.com/keithw1/LUAU)


### Medium Post
You can read the corresponding [Medium blog here](https://medium.com/@keithw_53739/reducing-your-aws-bill-765fa8a979bd)

## How it works?
LUAU utilizes amazon's tagging system to create a framework that can alert users about their unececessary expenditure and help act upon them.

## Installation Guide

### Before Cloning the Repo
1. Make sure you can use the AWS CLI on your machine and that you can access the environment you want to deploy LUAU to. 
2. Register an email account with SES that will be used to send email reports
3. Create an S3 Bucket that will be used to store the Lambda .ZIP source.
4. Create the following parameters in SSM Parameter Store
    * LAMBDA_CODE_BUCKET -- S3 Bucket Name
    * SES_EMAIL -- Email Address registered to SES in Step 1.
    * ADMIN_EMAIL -- Email Address that will receive the Admin Report. 

### After Cloning the Repo
1. In resources/env.properties, set the AWS_REGION to your desired region (default is us-west-2)
2. cd into the project root.
3. Run `python3 ./bin/create_templates.py`. This will create the SES Email templates used in the email reports
4. Run `./bin/build.sh`. This will generate the LUAU ZIP Artifact. You may need to edit the files permissions to run this
5. Run `./bin/deploy.sh`. This will deploy LUAU to your AWS Environment. You may need to edit the files permissions to run this

## Package Structure

```
├── bin
│   ├── build.sh -- Builds deployment package
│   ├── create_templates.py -- Used to create email templates in SES
│   └── deploy.sh -- Deploys lambdas via CloudFormation
├── low_use -- Parses low-use instances and sends reports
│   ├── report_parser.py -- Parses low-use report
│   └── reporter.py -- Tags instance as LowUse, Whitelisted, or Scheduled For Deletion. Also sends SES Emails and stops instances
├── requirements.txt
├── resources
│   ├── env.properties -- Parameters for Lambdas (SES Email, etc.)
│   ├── sam.yaml -- SAM template for deployment
│   └── templates
│       ├── admin_report.json -- Email template for Admin Report
│       └── low_use_report.json -- Email template for creator-level report
├── tagger
│   ├── asg_tagger.py -- Tags Autoscaling groups and their instances
│   ├── ec2_tagger.py -- Tags EC2 resources (Instances, AMIs, EBS Volumes, SGs)
│   └── parser -- Parses AWS API Event JSON
│       ├── __init__.py
│       ├── asg_event.py 
│       ├── base_event.py
│       └── ec2_event.py
└── util
    ├── aws.py -- Basic AWS Wrapper (SES, TrustedAdvisor, EC2, ASG)
    └── dynamo.py -- Wrapper for Dynamo tables (CRUD Access)

```
- **bin**: Contains build/deploy scripts    
- **low_use**: Will contain the Lambda function(s) responsible for processing Trusted Advisor data and emailing out the Low Use reports    
- **resources**: This contains configuration files used in the build/deploy processes. Right now it only contains the SAM template for the tagger.   
- **tagger**: This contains the Lambda functions responsible for auto-tagging AWS resources. Currently tags EC2, ASG, EBS, AMI, and Security Groups. This package also contains a parser subpackage used to parse the event data.     
- **test**: Where the tests go. Each Python package will have it's own test package called `[package_name]_test`. This also contains a folder with example event data for the events we want to handle.     
- **util**: This is a Python package that will contain utility modules that can be shared by the other packages. This includes things like AWS calls.    
