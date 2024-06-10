import json
import boto3
import os
import requests

def lambda_handler(event, context):
    slack_url = os.environ['SLACK_URL']
    resource_id = event['detail']['responseElements']['instancesSet']['items'][0]['instanceId']
    ec2_client = boto3.client('ec2')
    
    # 리소스의 태그 확인 fdsfdsf
    response = ec2_client.describe_tags(Filters=[
        {'Name': 'resource-id', 'Values': [resource_id]}
    ])
    
    if not response['Tags']:
        # 태그가 없으면 태그 추가
        ec2_client.create_tags(
            Resources=[resource_id],
            Tags=[{'Key': 'Name', 'Value': 'AutoTagged'}]
        )
        
        # Slack으로 알림 보내기
        message = f"Instance {resource_id} has been tagged automatically."
        requests.post(slack_url, json={'text': message})
    
    return {
        'statusCode': 200,
        'body': json.dumps('Tagging and notification complete')
    }