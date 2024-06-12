import json  # JSON 데이터를 다루기 위한 모듈
import boto3  # AWS 서비스와 상호 작용하기 위한 Boto3 모듈
import os  # 환경 변수를 다루기 위한 모듈
import requests  # HTTP 요청을 보내기 위한 모듈

def post_slack(message, slack_url):
    """
    Slack에 메시지를 보내는 함수
    :param message: 보낼 메시지 내용
    :param slack_url: Slack 웹훅 URL
    """
    send_data = {
        "text": message,  # 메시지를 JSON 형식으로 포맷팅
    }
    response = requests.post(slack_url, json=send_data)  # Slack 웹훅 URL로 HTTP POST 요청 보내기

def lambda_handler(event, context):
    """
    AWS Lambda 함수 핸들러
    :param event: 트리거 이벤트 데이터
    :param context: 실행 컨텍스트
    """
    event_detail = event['detail']  # 이벤트의 상세 정보 가져오기
    slack_url = os.environ['SLACK_URL']  # 환경 변수에서 Slack 웹훅 URL 가져오기
    resource_id = event_detail['responseElements']['instancesSet']['items'][0]['instanceId']  # 생성된 인스턴스의 ID 가져오기
    ec2_client = boto3.client('ec2')  # EC2 클라이언트 생성

    # EC2 인스턴스의 태그 가져오기
    response = ec2_client.describe_tags(Filters=[{'Name': 'resource-id', 'Values': [resource_id]}])
    post_slack(f"{response}", slack_url)  # 태그 정보를 Slack에 보내기
    tags = response.get('Tags', [])  # 태그 목록 가져오기, 기본값은 빈 리스트
    non_default_tags = [tag for tag in tags if tag['Key'] != 'Name']  # 기본 태그를 제외한 태그 목록 필터링

    if non_default_tags:
        # 기본 태그 외에 추가 태그가 있는 경우
        post_slack(f"Instance {resource_id} has additional tags: {non_default_tags}", slack_url)  # Slack에 추가 태그 정보 보내기
    else:
        # 기본 태그 외에 추가 태그가 없는 경우
        ec2_client.create_tags(
            Resources=[resource_id],
            Tags=[{'Key': 'Name', 'Value': 'AutoTagged'}]  # 'Name' 태그를 'AutoTagged'로 생성
        )
        post_slack(f"Instance {resource_id} has been tagged automatically.", slack_url)  # 태그 자동 생성 정보 Slack에 보내기
