[![pipeline status](https://gitlab.com/keithw1/LUAU/badges/master/pipeline.svg)](https://gitlab.com/keithw1/LUAU/commits/master)

[![coverage report](https://gitlab.com/keithw1/LUAU/badges/master/coverage.svg)](https://gitlab.com/keithw1/LUAU/commits/master)

# LUAU

## Package Structure

- LUAU/
    - bin/

        Contains build/deploy scripts
        
    - mailer/
    
        Will contain the Lambda function(s) responsible for processing Trusted Advisor data and emailing out the Low Use reports

    - resources/
    
        This contains configuration files used in the build/deploy processes. Right now it only contains the SAM template for the tagger.

    - tagger/ 
    
        This contains the Lambda functions responsible for auto-tagging AWS resources. Currently tags EC2, ASG, EBS, AMI, and Security Groups. This package also contains a parser subpackage used to parse the event data.

    - test/
    
        Where the tests go. Each Python package will have it's own test package called [package_name]_test. This also contains a folder with example event data for the events we want to handle. 

    - util/ 
    
        This is a Python package that will contain utility modules that can be shared by the other packages. This includes things like AWS calls. 