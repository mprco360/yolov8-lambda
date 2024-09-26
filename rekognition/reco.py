import boto3
from urllib.parse import urlparse
import requests
import PIL
from PIL import Image
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import boto3
import os
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime
import json
import calendar


class Recognition(object):
    """
    {
    "session_id": 123895,
    "image_url": "https://proctor360.s3.amazonaws.com/test/ai/6246_JCZoILhks1JkbO45r2MG_1724248639.jpg",
    "bucket_name": "proctor360",
    "organisation_id": "12345",
    "session_link": "vs12345",
    "exam_id": "12345",
    "student_session_id": 12345,
    "source_image":"face_photo/0067ZGCDO3e0TrUXzXFR-1588545008791-1588545006906.png"
}
    """

    def __init__(self, data):
        self.data = data
        self.bucket_name = data["bucket_name"]
        self.organisation_id = data["organisation_id"]
        self.session_link = data["session_link"]
        self.exam_id = data["exam_id"]
        self.student_session_id = data["student_session_id"]
        self.source_image = data["source_image"]
        self.recognition_agent = boto3.client('rekognition')

    def _draw_bounding_box(self, img, result_summary, fontsize=32, outline="#FF999C", width=10, radius=14,
                           threshold=30, labels_dict=None):
        print("result summary is ",result_summary)
        tablet_computer = {"laptop", "tv", "tablet", "book", "tablet_computer", "tablet computer"}
        cell_phone = {"cell_phone", "remote", "cell phone", "phone", "mobile phone"}
        if labels_dict is None:
            labels_dict = {"remote", "laptop", "tv", "cell_phone", "person"}
        draw = ImageDraw.Draw(img)
        width_,height_ = img.size
        for i in range(len(result_summary)):
            object_categ_dict = result_summary[i]
            print(object_categ_dict)
            tmp = threshold
            if object_categ_dict["name"] in labels_dict:
                if object_categ_dict["name"] in tablet_computer:
                    object_categ_dict["name"] = "tablet_computer"
                if object_categ_dict["name"] == "person":
                    tmp = 60
                if object_categ_dict["confidence"] > tmp / 100:
                    x0 = object_categ_dict["box"]["x1"]*width_
                    y0 = object_categ_dict["box"]["y1"]*height_
                    x1 = object_categ_dict["box"]["x2"]*width_
                    y1 = object_categ_dict["box"]["y2"]*height_
                    text = "{}: {}".format(object_categ_dict["name"], round(object_categ_dict["confidence"] * 100))
                    draw.rounded_rectangle((x0, y0, x1, y1), outline=outline,
                                           width=width, radius=radius)
                    print("draw",object_categ_dict["name"])
                    font = ImageFont.truetype("Acme-Regular.ttf", fontsize)
                    bbox = draw.textbbox((0, 0), text, font=font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                    width_image, _ = img.size
                    if x0 + text_width >= width_image:
                        x0 = width_image - text_width
                    if y0 - text_height <= 0:
                        y0 = text_height
                    draw.rounded_rectangle((x0, y0, x0 + text_width + 10, y0 + text_height + 10), outline=outline,
                                           width=2, radius=0)

                    draw.text((x0 + 5, y0), text, (255, 0, 0), font=font)
        return img

    def object_detection(self):
        bucket_name = self.data["src_bucket_name"]
        destination_ = self.data["src_destination"]
        labels = self.recognition_agent.detect_labels(
            Image={
                "S3Object": {
                    "Bucket": bucket_name,
                    "Name": destination_
                }
            },
            MaxLabels=100,
            MinConfidence=70.0

        )
        dict_ = {}
        list_labels = []
        for label in labels["Labels"]:
            dict_[label["Name"].lower()] = label["Confidence"]
            for instance in label["Instances"]:
                x0 = instance["BoundingBox"]["Left"]
                x1 = instance["BoundingBox"]["Left"] + instance["BoundingBox"]["Width"]
                y0 = instance["BoundingBox"]["Top"]
                y1 = instance["BoundingBox"]["Top"] + instance["BoundingBox"]["Height"]
                list_labels.append(
                    {
                        "name": label["Name"],
                        "confidence": instance["Confidence"],
                        "box": {
                            "x1": x0,
                            "x2": x1,
                            "y1": y0,
                            "y2": y1
                        }
                    }
                )

        return dict_, list_labels

    def face_match(self,s3_client,src_img,threshold=60):
        ground_truth = s3_client.Bucket(self.bucket_name).Object(self.data["source_image"]).get()
        ground_truth_img = BytesIO(ground_truth['Body'].read())
        img_byte_array = BytesIO()
        src_img = src_img.convert("RGB")
        src_img.save(img_byte_array,'JPEG')  # Use the original image format
        img_bytes = img_byte_array.getvalue()
        response = self.recognition_agent.compare_faces(
            SourceImage={'Bytes': ground_truth_img.getvalue()},
            TargetImage={'Bytes': img_bytes},
            SimilarityThreshold=threshold
        )

        # Process the response
        for face_match in response['FaceMatches']:
            similarity = face_match['Similarity']
            if similarity > threshold:
                return True

        if not response['FaceMatches']:
            print("No faces matched")
        return False

    def push_to_mongo(self, detected_objects, list_labels):
        s3_client = boto3.resource('s3')
        if "is_image_found" in self.data and "image" not in self.data:
            response = s3_client.Bucket(self.data["bucket_name"]).Object(self.data["src_destination"]).get()
            decoded_bytes = response['Body'].read()
            img = Image.open(BytesIO(decoded_bytes))
        else:
            decoded_bytes = bytes.fromhex(self.data["image"])
            img = Image.open(BytesIO(decoded_bytes))
        draw_img = self._draw_bounding_box(img, list_labels)
        detected_dict_formatted = []
        tablet_computer = {"laptop", "tv", "tablet", "book", "tablet_computer", "tablet computer"}
        cell_phone = {"cell_phone", "remote", "cell phone", "phone", "mobile phone"}
        if len(detected_objects) == 0:
            detected_dict_formatted.append({"name": "no_face", "confidence": 100})
        else:
            if "person" not in detected_objects:
                detected_dict_formatted.append({"name": "no_face", "confidence": 100})
            else:
                if not self.face_match(s3_client,img):
                    detected_dict_formatted.append({"name": "face_not_matched", "confidence": 100})
                for key in detected_objects:
                    key = key.strip()
                    key = key.lower()
                    if key == "people":
                        detected_dict_formatted.append({"name": f"multiple_people", "confidence":
                            detected_objects[key]})
                    elif key in tablet_computer:
                        detected_dict_formatted.append({"name": "tablet_computer",
                                                        "confidence": detected_objects[key]})
                    elif key in cell_phone:
                        detected_dict_formatted.append(
                            {"name": "cell_phone",
                             "confidence": detected_objects[key]})
                    else:
                        continue

        print("detected_object_dict\n")
        print(detected_dict_formatted)
        if len(detected_dict_formatted) > 0:
            buffer = BytesIO()
            img_ = draw_img.convert("RGB")
            img_.save(buffer, 'JPEG')
            buffer.seek(0)
            date = datetime.utcnow()
            utc_time = calendar.timegm(date.utctimetuple())
            s3_client.Bucket(self.bucket_name).upload_fileobj(buffer,
                                                              f'test/ai/yolo_{self.student_session_id}_{self.data["session_link"]}_{utc_time}.jpg',
                                                              ExtraArgs={'ContentType': 'image/jpeg'})
            date = datetime.utcnow()
            utc_time = calendar.timegm(date.utctimetuple())
            uri = os.environ['MONGO_URL']
            client = MongoClient(uri, server_api=ServerApi(version="1"))

            # Send a ping to confirm a successful connection
            try:
                client.admin.command('ping')
            except Exception as e:
                print(e)
                print("ping failed")

            db = client.proctor360
            collection = db.ai_live_labels
            post_data = {
                "labels": detected_dict_formatted,
                "face_matched": self.face_match(s3_client,img),
                "image": f'test/ai/yolo_{self.student_session_id}_{self.data["session_link"]}_{utc_time}.jpg',
                "organisation_id": self.data["organisation_id"],
                "session_link": self.data["session_link"],
                "student_session_id": self.data["student_session_id"],
                "exam_id": self.data["exam_id"],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "type": "rekognition",
            }
            print(post_data)
            result = collection.insert_one(post_data)
            return {
                'statusCode': 200,
                'body': json.dumps("found images")
            }

    def process(self):
        detected_objects,list_labels = self.object_detection()
        print(detected_objects)
        self.push_to_mongo(detected_objects,list_labels)


s = Recognition(
    {
    "session_id": 123895,
    "image_url": "https://proctor360.s3.amazonaws.com/test/ai/6246_JCZoILhks1JkbO45r2MG_1724248639.jpg",
    "bucket_name": "proctor360",
    "organisation_id": "12345",
    "session_link": "vs12345",
    "exam_id": "12345",
    "student_session_id": 12345,
    "source_image":"face_photo/0067ZGCDO3e0TrUXzXFR-1588545008791-1588545006906.png",
    "is_image_found" : True,
    "src_bucket_name" : "proctor360",
    "src_destination" : "test/ai/6246_JCZoILhks1JkbO45r2MG_1724248639.jpg",
    }
)

print(s.process())