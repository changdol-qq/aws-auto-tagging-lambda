import json
import boto3
import os
import requests

def post_slack(message, slack_url):
    send_data = {
        "text": message,
    }
    response = requests.post(slack_url, json=send_data)

def lambda_handler(event, context):
    event_detail = event['detail']
    slack_url = os.environ['SLACK_URL']
    resource_id =  event_detail['responseElements']['instancesSet']['items'][0]['instanceId']
    ec2_client = boto3.client('ec2')
    
    response = ec2_client.describe_tags(Filters=[{'Name': 'resource-id', 'Values': [resource_id]}])
    post_slack(f"{response}", slack_url)
    tags = response.get('Tags', [])
    non_default_tags = [tag for tag in tags if tag['Key'] != 'Name']
    if non_default_tags:
            post_slack(f"Instance {resource_id} has additional tags: {non_default_tags}", slack_url)
    else:
        ec2_client.create_tags(
            Resources=[resource_id],
            Tags=[{'Key': 'Name', 'Value': 'AutoTagged'}]
        )
        post_slack(f"Instance {resource_id} has been tagged automatically.", slack_url)
