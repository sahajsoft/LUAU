import boto3
import json
from botocore.exceptions import ClientError

ses = boto3.client('ses', region_name = 'us-west-2')

def create_template_from_file(file_path):
    with open(file_path) as f:
        template = json.load(f)

    template['HtmlPart'] = ''.join(template['HtmlPart'])
    template['TextPart'] = ''.join(template['TextPart'])

    try:
        ses.get_template(TemplateName=template['TemplateName'])
    except ClientError as e:
        if e.response['Error']['Code'] == 'TemplateDoesNotExist':
            ses.create_template(Template=template)
    else:
        ses.update_template(Template=template)


create_template_from_file('./resources/templates/low_use_report.json')
create_template_from_file('./resources/templates/admin_report.json')

    