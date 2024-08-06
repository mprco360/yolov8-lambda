import json
from module import Prediction
import requests
import PIL
from PIL import Image
from io import BytesIO
import boto3
import os
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import datetime
from datetime import datetime
import math



# Create an S3 client


# async def get_image(image_url):
#         try :
#             response = requests.get(image_url)
#             return response.content
#         except:
#             raise InterruptedError("Image not found")
        
# async def upload_image(buffer,bucket_name,session_id):
#     try:
#         s3_client = boto3.resource('s3')
#         s3_client.Bucket(bucket_name).upload_fileobj(buffer,  f'test/ai/{session_id}.jpg', ExtraArgs={'ContentType': 'image/jpeg'})
#     except:
#         raise InterruptedError("upload not finshed")


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
    print(data)
    if data:
        if "image" in data and "source_dir" in data and "destination_dir" in data:
            session_id = data["session_id"]
            source = data["source_dir"]
            destination = data["destination_dir"]
            bucket_name = data["bucket_name"]
            p = Prediction(source,destination)
            if "object_dict" in data:
                object_dict = data["object_dict"]
            else:
                object_dict = {
                    "imagemode":"False",
                    "outline":"#FF999D",
                    "framerate":20,
                    "fontsize":16,
                    "radius":4,
                    "width":4,
                    "threshold":75
                }
            decoded_bytes = bytes.fromhex(data["image"])
            img = Image.open(BytesIO(decoded_bytes))
            #img = img.resize((640,480))b6948ae9779f
            image_dict = {"session_id":session_id,"image":img}
            detected_objects,img = p.process(object_dict,imagemode=True,image_dict=image_dict)
            response = {
                    "session_id": session_id,
                    "detected_objects": detected_objects
                }
            detected_dict_formatted = []
            for key in detected_objects:
                if detected_objects[key]["count"] > 1:
                    detected_dict_formatted.append({"name":f"multiple_{key}'s","confidence":round(sum(detected_objects[key]["confidence"])/detected_objects[key]["count"],4)})
                for i in range(detected_objects[key]["count"]):
                    detected_dict_formatted.append({"name":f"{key}_{i}","confidence":detected_objects[key]["confidence"][i]}) 
            print(detected_dict_formatted)
            buffer = BytesIO()
            img.save(buffer, 'JPEG')
            buffer.seek(0)
            s3_client.Bucket(bucket_name).upload_fileobj(buffer,  f'test/ai/{session_id}.jpg', ExtraArgs={'ContentType': 'image/jpeg'})

            uri = os.environ['MONGO_URL']
            print(f"uri is {uri}")

            # Create a new client and connect to the server
            client = MongoClient(uri, server_api=ServerApi('1'))

            # Send a ping to confirm a successful connection
            try:
                client.admin.command('ping')
                print("Pinged your deployment. You successfully connected to MongoDB!")
            except Exception as e:
                print(e)
            
            db = client.proctor360
            collection = db.ai_live_labels
            data = {
                "labels": detected_dict_formatted,
                "face_matched": True,
                "image": f'test/ai/{session_id}.jpg',
                "organisation_id": 1,
                "session_link": "vZjLNh5O9wE3C3te0PqY",
                "student_session_id": 6211,
                "exam_id": 2236,
                "created_at": {"$date": datetime.utcnow()},
                "updated_at": {"$date": datetime.utcnow()}
            }

            result = collection.insert_one(data)
            return {
                'statusCode':200,
                'body': json.dumps(response)
            }
        else:
            return {
                    'statusCode':400,
                    'body': json.dumps({"error": "Image url is required"})
                }

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "hello world",
            # "location": ip.text.replace("\n", "")
        }),
    }
