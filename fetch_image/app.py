import boto3
import json
import os
import requests
from urllib.parse import urlparse


def fetch_image_handler(event, context):
    sqs = boto3.client('sqs')
    queue_url = os.environ['QUEUE_URL']
    try:
        data = json.loads(event["body"])
    except:
        if "body" in event:
            data = event["body"]
        else:
            data = event
    if data:
        missing_string = ""
        if "image_url" not in data:
            missing_string += " image_url"
        if "organisation_id" not in data:
            missing_string += " organisation_id"
        if "session_link" not in data:
            missing_string += " session_link"
        if "student_session_id" not in data:
            missing_string += " student_session_id"
        if "exam_id" not in data:
            missing_string += "exam_id"
        if missing_string != "":
            return {
                'statusCode': 400,
                'body': json.dumps(f'Missing parameters {missing_string}')
            }
        image_url = data["image_url"]
        try:
            if "s3" in image_url:
                s3_client = boto3.resource('s3')
                parsed_url = urlparse(image_url)
                bucket_name = parsed_url.netloc.split(".")[0]
                destination_ = parsed_url.path.lstrip("/")
                response = s3_client.Bucket(bucket_name).Object(destination_).get()
                if response and response["ResponseMetadata"]['HTTPStatusCode'] == 200:
                    data["is_image_found"] = True
                    data["src_bucket_name"] = bucket_name
                    data["src_destination"] = destination_
                else:
                    return {
                        'statusCode': 404,
                        'body': json.dumps('Failed to fetch image')
                    }
            else:
                response = requests.get(image_url)
                if response.status_code == 200:
                    data["image"] = response.content.hex()
                else:
                    return {
                        'statusCode': response.status_code,
                        'body': json.dumps('Failed to fetch image')
                    }
            sqs.send_message(
                QueueUrl=queue_url,
                MessageBody=json.dumps(data)
            )
            return {
                'statusCode': 200,
                'body': json.dumps('Image fetched and sent to SQS successfully')
            }
        except:
            return {
                'statusCode': 404,
                'body': json.dumps('Failed to fetch image')
            }
