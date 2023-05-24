from flask import request, jsonify
from PIL import Image
from io import BytesIO
import base64
import json
import torch
from models1 import Plant, db
from utils1 import image_to_base64, result_to_json

class_names = ['Clusia', 'Fan-Palms', 'Lvicks plant', 'Pachira', 'Wind orchid', 'caladium',
               'carnation', 'creeping fig', 'croton', 'eucalyptus', 'freesia', 'geranium',
               'poinsettia', 'ribbon plant']

model_path = r'D:/sources-Garden-Genie/new_best.pt'
model = torch.hub.load('ultralytics/yolov5', 'custom', path=model_path, force_reload=True)

def analyze_image():
    # 요청으로 받은 이미지
    if 'image' not in request.files:
        return jsonify({"error": "No image found in request."}), 400
    img = Image.open(BytesIO(request.files['image'].read()))

    # 이미지를 640x640 크기로 변환
    img = img.resize((640, 640))
    img = img.convert('RGB')

    # 이미지 분석
    results = model(img)
    results.print()

    # 분석 결과를 JSON 형태로 변환
    result = result_to_json(image_to_base64(img), results)
    # 결과를 DB에 저장
    plant_name = get_plant_name(result)
    save_result(img, plant_name)

    return result


def get_plant_name(result):
    # 분석 결과에서 식물 이름 추출
    data = json.loads(result)
    if "results" in data:
        results = data["results"]
        if results:
            return results[0]["label"]
    return "Unknown"


def save_result(image, plant_name):
    # 이미지를 base64로 인코딩
    image_base64 = image_to_base64(image)

    # DB에 결과 저장
    #plant = Plant(plt_name=plant_name, plt_img=image_base64)
    plant = Plant(plt_name=plant_name)
    db.session.add(plant)
    db.session.commit()