import pathlib
import numpy as np
import PIL.Image
from PIL import Image, ImageDraw, ImageFont
import ultralytics
from ultralytics.models import YOLO
import torch
import matplotlib.pyplot as plt
import PIL
import argparse
import deepface
from deepface import DeepFace


class Prediction(object):
    def __init__(self, source_name, target_name, device="cpu"):
        self.source = source_name
        self.target = target_name
        target_path = pathlib.Path(self.target)
        if not target_path.is_dir():
            target_path.mkdir(parents=True, exist_ok=True)
        self.model = YOLO("yolov10x.pt")
        if device == "cuda" and torch.cuda.is_available():
            self.model.to(device="cuda")

    def _process_video(self, src, dict_, frame_rate=20, threshold=30):
        result = self.model(src, stream=True)
        subject_id = str(src).split("/")[-2]
        subject_name = str(src).split("/")[-1]
        save_dir = pathlib.Path(self.target + "/" + subject_id)
        if not save_dir.is_dir():
            save_dir.mkdir(parents=True, exist_ok=True)
        frame_count = 0
        while True:
            s = next(result)
            result_summary = s.summary()
            default_img = s.orig_img
            if frame_count % frame_rate == 0:
                img = self._draw_bounding_box(default_img,
                                              result_summary,
                                              threshold=threshold,
                                              fontsize=dict_["fontsize"],
                                              outline=dict_["outline"],
                                              width=dict_["width"],
                                              radius=dict_["radius"],
                                              )
                img.save(str(save_dir) + "/" + f"{subject_name}_{frame_count}.jpeg")
            frame_count += 1

    def _filter(self, result_summary, threshold=30):
        new_list = []
        print("res filter",result_summary)
        for i in range(len(result_summary)):
            if result_summary[i]["confidence"] > threshold / 100:
                new_list.append(result_summary[i])
        return new_list

    def _process_image(self, img, session_id, threshold=30):
        s = self.model(img)
        result_summary = s[0].summary()
        default_img = s[0].orig_img
        img = self._draw_bounding_box(default_img, result_summary, threshold=threshold)
        result_summary = self._filter(result_summary, threshold=threshold)
        return result_summary, img

    def _draw_bounding_box(self, img, result_summary, fontsize=32, outline="#FF999C", width=10, radius=14,
                           threshold=30, labels_dict=None):
        tablet_computer = {"laptop", "tv", "cell_phone", "remote", "tablet"}
        if labels_dict is None:
            labels_dict = {"remote", "laptop", "tv", "cell_phone", "person"}
        img = Image.fromarray(img)
        draw = ImageDraw.Draw(img)
        for i in range(len(result_summary)):
            object_categ_dict = result_summary[i]
            print(object_categ_dict)
            tmp = threshold
            if object_categ_dict["name"] in labels_dict:
                if object_categ_dict["name"] in tablet_computer:
                    object_categ_dict["name"] = "tablet_computer"
                if object_categ_dict["name"] == "person":
                    tmp = 30
                if object_categ_dict["confidence"] > tmp / 100:
                    x0 = object_categ_dict["box"]["x1"]
                    y0 = object_categ_dict["box"]["y1"]
                    x1 = object_categ_dict["box"]["x2"]
                    y1 = object_categ_dict["box"]["y2"]
                    text = "{}: {}".format(object_categ_dict["name"], round(object_categ_dict["confidence"] * 100))
                    draw.rounded_rectangle((x0, y0, x1, y1), outline=outline,
                                           width=width, radius=radius)
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

    def process(self, boundingbox_dict, frame_rate=20, image_dict=None, imagemode=True, threshold=30):
        if not imagemode:
            src_path = list(pathlib.Path(self.source).glob("*/*.webm")) + list(
                pathlib.Path(self.source).glob("*/*.avi"))
            for pt in src_path:
                self._process_video(pt, boundingbox_dict, frame_rate=frame_rate, threshold=threshold)
        if imagemode and image_dict:
            img = image_dict["image"]
            session_id = image_dict["session_id"]
            detected_objects, img = self._process_image(img, session_id=session_id)
            new_dict = {}
            for dict_ in detected_objects:
                if round(dict_["confidence"] * 100, 2) > threshold:
                    if dict_["name"] == "person" and dict_["confidence"] > 0.3:
                        if dict_["name"] in new_dict:
                            new_dict[dict_["name"]]["confidence"].append(round(dict_["confidence"] * 100, 2))
                            new_dict[dict_["name"]]["count"] += 1
                        else:
                            new_dict[dict_["name"]] = {"count": 1, "confidence": [round(dict_["confidence"] * 100, 2)]}
                    else:
                        if dict_["name"] in new_dict:
                            new_dict[dict_["name"]]["confidence"].append(round(dict_["confidence"] * 100, 2))
                            new_dict[dict_["name"]]["count"] += 1
                        else:
                            new_dict[dict_["name"]] = {"count": 1, "confidence": [round(dict_["confidence"] * 100, 2)]}
            return new_dict, img


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--source', type=str, help='destination of dataset files')
    parser.add_argument('-d', '--destination', type=str, help='destination of the target images')
    # to migrate to aws, use username_date , this destination parameter is redundant
    # use asynchronus function to 
    parser.add_argument("-m", '--imagemode', type=str, help="image or video mode", default="False")
    parser.add_argument("-o", '--outline', type=str, help="color of the bounding box", default="#FF999D")
    parser.add_argument('-f', '--framerate', type=int, help='framerate', default=20)
    parser.add_argument("-font", "--fontsize", type=int, help="font of the bounding box text", default=16)
    parser.add_argument("-r", "--radius", type=int, help="radius of the bounding box", default=4)
    parser.add_argument("-w", "--width", type=int, help="width of the bounding box", default=4)
    parser.add_argument("-t", "--threshold", type=int, help="threshold of the prediction", default=75)

    args = parser.parse_args()
    imgmode = bool(args.imagemode == "True")
    s = Prediction(args.source, args.destination)
    dict_ = {"fontsize": args.fontsize, "radius": args.radius, "width": args.width, "threshold": args.threshold,
             "outline": args.outline}
    print(args.source, args.destination, imgmode)
    print(s.process(dict_, frame_rate=args.framerate, imagemode=imgmode, threshold=args.threshold))
