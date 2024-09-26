import boto3
import json
from reco import Recognition


def rekognition_handler(event, context):
    print(event)
    for record in event["Records"]:
        tmp_rec = record
    try:
        data = json.loads(tmp_rec["body"])
    except:
        if "body" in tmp_rec:
            data = tmp_rec["body"]
        else:
            data = tmp_rec

    if data:
        reco_class = Recognition(data)
        print(data)
        if "image" in data or "is_image_found" in data:
            reco_class.process()
            try:
                reco_class.process()
                return {
                    "statusCode": 200,
                    "body": json.dumps({
                        "message": "successfully processed image",
                        # "location": ip.text.replace("\n", "")
                    }),
                }
            except:
                return {
                    "statusCode": 400,
                    "body": json.dumps({
                        "message": "failed to process image",
                        # "location": ip.text.replace("\n", "")
                    }),
                }
