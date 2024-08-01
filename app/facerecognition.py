import PIL
import argparse
import numpy as np
from PIL import Image
from ultralytics import YOLO
from module import Prediction
import pathlib
class FaceRecognition(Prediction):
    def __init__(self, source_name, target_name, device="cuda"):
        super().__init__(source_name, target_name, device)
        self.face_model = YOLO("yolov8l-face.pt")
    
    def _filter_threshold(self,predicted_dict,threshold):
        updated_objects = []
        for dict_ in predicted_dict:
            if dict_["confidence"]*100 > threshold:
                updated_objects.append(dict_)
        return updated_objects
    
    def _intersection_over_union(self,face_bbox,objects_bbox):
        x1_min, y1_min, x1_max, y1_max = face_bbox
        x2_min, y2_min, x2_max, y2_max = objects_bbox
        x_inter_min = max(x1_min, x2_min)
        y_inter_min = max(y1_min, y2_min)
        x_inter_max = min(x1_max, x2_max)
        y_inter_max = min(y1_max, y2_max)
        inter_area = max(0, x_inter_max - x_inter_min) * max(0, y_inter_max - y_inter_min)

        bbox1_area = (x1_max - x1_min) * (y1_max - y1_min)
        bbox2_area = (x2_max - x2_min) * (y2_max - y2_min)
        union_area = bbox1_area + bbox2_area - inter_area
        iou = inter_area / min(bbox1_area,bbox2_area)
        iou_percentage = iou * 100
        return iou_percentage
    
    def _make_predictions(self,img,iou_threshold,objects_pred=None,filter_threshold=None):
        img = Image.fromarray(img)
        if objects_pred is None and filter_threshold is None:
            objects_pred = self.model(img)
            objects_pred = objects_pred[0].summary()
            self._filter_threshold(objects_pred,filter_threshold)
        face_pred = self.face_model(img)
        face_pred = face_pred[0].summary()
        i = 0
        new_pred_list = []
        for i in range(len(face_pred)):
            for j in range(len(objects_pred)):
                if objects_pred[j]["name"] == "person":
                    bbox1 = (objects_pred[j]["box"]["x1"],objects_pred[j]["box"]["y1"],objects_pred[j]["box"]["x2"],objects_pred[j]["box"]["y2"])
                    bbox2 = (face_pred[i]["box"]["x1"],face_pred[i]["box"]["y1"],face_pred[i]["box"]["x2"],face_pred[i]["box"]["y2"])
                    if self._intersection_over_union(bbox2,bbox1) > iou_threshold:
                        print(self._intersection_over_union(bbox2,bbox1))
                        print(face_pred[i])
                        print(objects_pred[j])
                        new_pred_list.append(face_pred[i])
        return new_pred_list
    
    def _process_image(self,img,session_id,threshold):
        pred_dict = self._make_predictions(img,threshold)
        img = self._draw_bounding_box(img,pred_dict)
        img.save(self.target+"/"+f"{session_id}.jpg")
    
    def _process_video(self,src,dict_,frame_rate=20,threshold=70,iou_threshold=99):
        result = self.model(src,stream=True)
        subject_id = str(src).split("/")[-2]
        subject_name = str(src).split("/")[-1]
        save_dir = pathlib.Path(self.target+"/"+subject_id)
        if not save_dir.is_dir():
            save_dir.mkdir(parents=True,exist_ok=True)
        frame_count = 0
        while True:
            try:
                s = next(result)
                result_summary = s.summary()
                default_img = s.orig_img
                if frame_count%frame_rate == 0:
                    result_summary = self._filter_threshold(result_summary,threshold)
                    result_summary = self._make_predictions(np.array(default_img),iou_threshold,objects_pred=result_summary,filter_threshold=threshold)
                    img = self._draw_bounding_box(default_img,
                                                    result_summary,
                                                    threshold=threshold,
                                                    fontsize=dict_["fontsize"],
                                                    outline=dict_["outline"],
                                                    width=dict_["width"],
                                                    radius=dict_["radius"],
                                                    )
                    img.save(str(save_dir)+"/"+f"{subject_name}_{frame_count}.jpeg")
                frame_count += 1
            except:
                break
    
    def process(self,boundingbox_dict,frame_rate=20,image_dict = None,imagemode = True,threshold=70,iou_threshold=99):
        print(imagemode,type(imagemode))
        if not imagemode:
            src_path = list(pathlib.Path(self.source).glob("*/*.webm"))+list(pathlib.Path(self.source).glob("*/*.avi"))
            print(src_path)
            for pt in src_path:
                self._process_video(pt,boundingbox_dict,frame_rate=frame_rate,threshold=threshold,iou_threshold=iou_threshold)
        if imagemode and image_dict:
            img = image_dict["image"]
            session_id = image_dict["session_id"]
            detected_objects = self._process_image(img,session_id=session_id,threshold=iou_threshold)
            new_dict = {}
            for dict_ in detected_objects:
                if round(dict_["confidence"]*100,2) > threshold:
                    if dict_["name"] in new_dict:
                        new_dict[dict_["name"]]["confidence"].append(round(dict_["confidence"]*100,2))
                        new_dict[dict_["name"]]["count"] += 1
                    else:
                        new_dict[dict_["name"]] = {"count":1,"confidence":[round(dict_["confidence"]*100,2)]}
            return new_dict
    
#c = FaceRecognition("/home/sonu/intern/OEP database","/home/sonu/intern/face_results")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--source', type=str, help='destination of dataset files')
    parser.add_argument('-d', '--destination', type=str, help='destination of the target images')
    parser.add_argument("-m",'--imagemode',type=str,help="image or video mode",default="False")
    parser.add_argument("-o",'--outline',type=str,help="color of the bounding box",default="#FF999D")
    parser.add_argument('-f', '--framerate', type=int, help='framerate',default=20)
    parser.add_argument("-font","--fontsize",type=int,help="font of the bounding box text",default=16)
    parser.add_argument("-r","--radius",type=int,help="radius of the bounding box",default=4)
    parser.add_argument("-w","--width",type=int,help="width of the bounding box",default=4)
    parser.add_argument("-t","--threshold",type=int,help="threshold of the prediction",default=75)
    parser.add_argument("-it","--iouthreshold",type=int,help="threshold of the iou",default=99)
    
    args = parser.parse_args()
    imgmode = bool(args.imagemode == "True")
    s = FaceRecognition(args.source,args.destination)
    dict_ = {"fontsize":args.fontsize,"radius":args.radius,"width":args.width,"threshold":args.threshold,"outline":args.outline}
    print(args.source,args.destination,imgmode)
    print(s.process(dict_,frame_rate=args.framerate,imagemode=imgmode,threshold=args.threshold,iou_threshold=args.iouthreshold))

