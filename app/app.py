import calendar
import json

import numpy as np

from module import Prediction
import requests
import PIL
from PIL import Image
from io import BytesIO
import boto3
import os
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime
import math


def lambda_handler(event, context):
    """Sample pure Lambda function

    Parameters
    ----------
    event: dict, required
        API Gateway Lambda Proxy Input Format

        Event doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-input-format

    context: object, required
        Lambda Context runtime methods and attributes

        Context doc: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

    Returns
    ------
    API Gateway Lambda Proxy Output Format: dict

        Return doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html
    """
    s3_client = boto3.resource('s3')
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
        print(data)
        if "image" in data or "is_image_found" in data:
            session_id = data["student_session_id"]
            source = ""
            destination = "."
            bucket_name = data["bucket_name"]
            p = Prediction(source, destination)
            if "object_dict" in data:
                object_dict = data["object_dict"]
            else:
                object_dict = {
                    "imagemode": "False",
                    "outline": "#FF999D",
                    "framerate": 20,
                    "fontsize": 16,
                    "radius": 4,
                    "width": 4,
                    "threshold": 75
                }
            if "is_image_found" in data and "image" not in data:
                response = s3_client.Bucket(data["src_bucket_name"]).Object(data["src_destination"]).get()
                decoded_bytes = response['Body'].read()
                img = Image.open(BytesIO(decoded_bytes))
            else:
                decoded_bytes = bytes.fromhex(data["image"])
                img = Image.open(BytesIO(decoded_bytes))
            
            image_dict = {"session_id": session_id, "image": img}
            detected_objects, img = p.process(object_dict, imagemode=True, image_dict=image_dict)
            response = {
                "session_id": session_id,
                "detected_objects": detected_objects
            }
            detected_dict_formatted = []
            labels_set = {"remote", "laptop", "tv", "cell_phone", "person", "tablet", "persons", "book","cell phone"}
            tablet_computer = {"laptop", "tv", "tablet", "book", "tablet_computer"}
            cell_phone = {"cell_phone", "remote","cell phone"}
            if len(detected_objects) == 0:
                detected_dict_formatted.append({"name": "no_face", "confidence": 100})
            else:
                if "person" not in detected_objects:
                    detected_dict_formatted.append({"name": "no_face", "confidence": 100})
                else:
                    for key in detected_objects:
                        key = key.strip()
                        if key == "person" and detected_objects[key]["count"] > 1:
                            detected_dict_formatted.append({"name": f"multiple_people", "confidence":
                                max(detected_objects[key]["confidence"])})
                        else:
                            if key in tablet_computer:
                                detected_dict_formatted.append({"name": "tablet_computer",
                                                                "confidence": max(detected_objects[key]["confidence"])})
                            elif key in cell_phone:
                                detected_dict_formatted.append(
                                    {"name": "cell_phone",
                                     "confidence": max(detected_objects[key]["confidence"])})
                            else:
                                continue

            print(detected_dict_formatted)
            print(detected_objects)
            if len(detected_dict_formatted) > 0:
                buffer = BytesIO()
                img_ = img.convert("RGB")
                img_.save(buffer, 'JPEG')
                buffer.seek(0)
                date = datetime.utcnow()
                utc_time = calendar.timegm(date.utctimetuple())
                s3_client.Bucket(bucket_name).upload_fileobj(buffer,
                                                             f'test/ai/yolo_{session_id}_{data["session_link"]}_{utc_time}.jpg',
                                                             ExtraArgs={'ContentType': 'image/jpeg'})

                uri = os.environ['MONGO_URL']
                client = MongoClient(uri, server_api=ServerApi(version="1"))

                # Send a ping to confirm a successful connection
                try:
                    client.admin.command('ping')
                except Exception as e:
                    print(e)

                db = client.proctor360
                collection = db.ai_live_labels
                post_data = {
                    "labels": detected_dict_formatted,
                    "face_matched": data["face_match"],
                    "image": f'test/ai/yolo_{session_id}_{data["session_link"]}_{utc_time}.jpg',
                    "organisation_id": data["organisation_id"],
                    "session_link": data["session_link"],
                    "student_session_id": data["student_session_id"],
                    "exam_id": data["exam_id"],
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "type": "yolo",
                }
                print(post_data)
                result = collection.insert_one(post_data)
                return {
                    'statusCode': 200,
                    'body': json.dumps(response)
                }
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({"error": "Image url is required"})
            }
    else:
        return {
            'statusCode': 400,
            'body': json.dumps({"error": "Image url is required"})
        }
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "hello world",
            # "location": ip.text.replace("\n", "")
        }),
    }
