import boto3
import json
import os
import requests
def fetch_image_handler(event,context):
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
        if "image_url" in data and "source_dir" in data and "destination_dir" in data:
            image_url = data["image_url"]
            try :
                if "s3" in image_url:
                    s3_client = boto3.resource('s3')
                response = requests.get(image_url)
                if response.status_code == 200:
                    data["image"] = response.content.hex()
                    sqs.send_message(
                    QueueUrl=queue_url,
                    MessageBody=json.dumps(data)
                    )
                    return {
                        'statusCode': 200,
                        'body': json.dumps('Image fetched and sent to SQS successfully')
                    }
                else:
                    return {
                        'statusCode': response.status_code,
                        'body': json.dumps('Failed to fetch image')
                    }
            except:
                return {
                        'statusCode': 404,
                        'body': json.dumps('Failed to fetch image')
                    }