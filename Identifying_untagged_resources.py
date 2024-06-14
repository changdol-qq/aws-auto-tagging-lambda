import boto3
import json
import requests
import os

def lambda_handler(event, context):
    config_client = boto3.client('config')
    ec2_client = boto3.client('ec2')
    
    # AWS Config에서 지원하는 모든 리소스 타입 목록
    resource_types = [
        'AWS::EC2::Instance',
        # 다른 리소스 타입을 추가
    ]

    all_resources = []

    for resource_type in resource_types:
        response = config_client.list_discovered_resources(resourceType=resource_type)
        resources = response.get('resourceIdentifiers', [])
        all_resources.extend(resources)

    tag_info = []
    slack_message = ""

    for resource in all_resources:
        resource_type = resource["resourceType"]
        resource_id = resource["resourceId"]

        if resource_type == "AWS::EC2::Instance":
            # EC2 리소스의 태그 가져오기
            tags_response = ec2_client.describe_tags(
                Filters=[
                    {'Name': 'resource-id', 'Values': [resource_id]}
                ]
            )
            tags = tags_response.get('Tags', [])
            tag_info.append({
                "resourceId": resource_id,
                "tags": tags
            })
            if not tags:
                # 태그가 없는 리소스에 태그 추가
                ec2_client.create_tags(
                    Resources=[resource_id],
                    Tags=[{'Key': "Auto", 'Value': "AutoTagged"}]
                )
                slack_message += f"Tagged resource {resource_id} with Auto=AutoTagged\n"

    # Slack에 메시지 전송
    if slack_message:
        send_slack_message(slack_message)

    # 결과 출력
    print(json.dumps(tag_info, indent=2))

    return {
        'statusCode': 200,
        'body': tag_info
    }

def send_slack_message(message):
    webhook_url = os.environ['SLACK_URL']
    slack_data = {'text': message}
    
    response = requests.post(
        webhook_url, data=json.dumps(slack_data),
        headers={'Content-Type': 'application/json'}
    )
    
    if response.status_code != 200:
        raise ValueError(f"Request to slack returned an error {response.status_code}, the response is:\n{response.text}")