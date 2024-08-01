import flask
import PIL
from PIL import Image
from io import BytesIO
from module import Prediction
from flask import Flask,request,jsonify
import requests

app = Flask(__name__)

@app.route("/detect",methods=["POST"])
def detect():
    """
    need to ask for bucket_name
    """
    data = request.get_json()
    if data:
        if "image_url" in data and "source_dir" in data and "destination_dir" in data:
            try:
                image_url = data["image_url"]
                session_id = data["session_id"]
                source = data["source_dir"]
                destination = data["destination_dir"]
                
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
                
                try :
                    response = requests.get(image_url)
                except:
                    return jsonify({"error": "image url is invalid"}), 400
                img = Image.open(BytesIO(response.content))
                #img = img.resize((640,480))
                image_dict = {"session_id":session_id,"image":img}
                detected_objects = p.process(object_dict,imagemode=True,image_dict=image_dict)
                
                response = {
                        "session_id": session_id,
                        "detected_objects": detected_objects
                    }
                return jsonify(response)
            except:
                return jsonify({"error": "Image processing failed check if image url is valid"}), 400
        else:
            return jsonify({"error": "Image url is required"}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0",port=8080)
    
#bucketname
#path /test/ai/image_name

            