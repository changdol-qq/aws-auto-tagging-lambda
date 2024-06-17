import boto3
import json
import requests
import os

def lambda_handler(event, context):
    # AWS Config 및 EC2 클라이언트 생성
    config_client = boto3.client('config')
    ec2_client = boto3.client('ec2')

    # AWS Config에서 지원하는 리소스 타입 목록
    resource_types = [
        'AWS::EC2::Instance',
        # 다른 리소스 타입을 추가
    ]
    slack_message = ""

    all_resources = []
    # 각 리소스 타입에 대해 발견된 리소스를 all_resources 리스트에 추가
    for resource_type in resource_types:
        response = config_client.list_discovered_resources(resourceType=resource_type)
        resources = response.get('resourceIdentifiers', [])
        all_resources.extend(resources)

    
    # 각 리소스 타입에 대해 발견된 리소스를 순회하며 태그 정보를 확인 및 추가
    for resource_type in resource_types:
        try:
            response = config_client.list_discovered_resources(resourceType=resource_type)
            resources = response.get('resourceIdentifiers', [])
            for resource in resources:
                resource_id = resource["resourceId"]

                if resource_type == "AWS::EC2::Instance":
                    try:
                        # EC2 인스턴스의 태그 가져오기
                        tags_response = ec2_client.describe_tags(
                            Filters=[
                                {'Name': 'resource-id', 'Values': [resource_id]}
                            ]
                        )
                        tags = tags_response.get('Tags', [])
                        if not tags:
                            # 태그가 없는 리소스에 태그 추가
                            ec2_client.create_tags(
                                Resources=[resource_id],
                                Tags=[{'Key': "AutoTagged", 'Value': "True"}]
                            )
                            # Slack 메시지에 태그 추가 정보 기록
                            slack_message += f"리소스 ID:{resource_id}에 태그를 완료하였습니다. AutoTagged=True\n"
                    except Exception as e:
                        print(f"Error processing resource {resource_id}: {e}")
        except Exception as e:
            print(f"Error listing resources for type {resource_type}: {e}")                

    

    # Slack에 메시지 전송
    if slack_message:
        try:
            send_slack_message(slack_message)
        except Exception as e:
            print(f"Error sending Slack message: {e}")

    return {
        'statusCode': 200,
        'body': 'Execution completed'
    }

def send_slack_message(message):
    # 환경 변수에서 Slack 웹훅 URL 가져오기
    webhook_url = os.environ['SLACK_URL']
    slack_data = {'text': message}
    
    # Slack에 POST 요청 보내기
    response = requests.post(
        webhook_url, data=json.dumps(slack_data),
        headers={'Content-Type': 'application/json'}
    )
    
    # 요청 실패 시 예외 발생
    if response.status_code != 200:
        raise ValueError(f"Request to slack returned an error {response.status_code}, the response is:\n{response.text}")