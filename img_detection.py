from PIL import Image
import os
from io import BytesIO
import base64
import json
from google.cloud import storage
import torch
from db_models import Plant, db
from dotenv import load_dotenv
from flask import Flask, request, render_template, jsonify

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS')
db.init_app(app)

# 클래스 이름
class_names = ['Clusia', 'Fan-Palms', 'Lvicks plant', 'Pachira', 'Wind orchid', 'caladium',
               'carnation', 'creeping fig', 'croton', 'eucalyptus', 'freesia', 'geranium',
               'poinsettia', 'ribbon plant']

# GCS 클라이언트 초기화
storage_client = storage.Client.from_service_account_json('D:/flask-Garden-Genie/garden-genie-key.json')

# 버킷 이름 설정
bucket_name = 'garden_genie_image'

# 모델 로드
model_path = r'D:/sources-Garden-Genie/new_best.pt'
model = torch.hub.load('ultralytics/yolov5', 'custom', path=model_path, force_reload=True)

# 이미지를 base64 문자열로 변환하는 함수
def image_to_base64(image):
    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue())
    return img_str.decode('utf-8')

# 분석 결과를 JSON 형태로 변환하는 함수
def result_to_json(image, results):
    unique_labels = set()  # 레이블 중복 제거
    labels = []
    if len(results.xyxy[0]) == 0:
        result_dict = {"image": image, "label": "No object detected"}
    else:
        result_dict = {"image": image, "label": ""}
        for result in results.xyxy[0]:
            label = class_names[int(result[5])]
            if label not in unique_labels:
                labels.append(label)
                unique_labels.add(label)
        if labels:
            result_dict["label"] = labels[0]
    return json.dumps(result_dict)

# def result_to_json(image, results):
#     unique_labels = set() # 레이블 중복 제거
#     if len(results.xyxy[0]) == 0:
#         result_dict = {"image": image, "results": [{"label": "No object detected"}]}
#     else:
#         result_dict = {"image": image, "results": []}
#         for result in results.xyxy[0]:
#             label = class_names[int(result[5])]
#             if label not in unique_labels:
#                 result_dict["results"].append({"label": label})
#                 unique_labels.add(label)
#     return json.dumps(result_dict)

# 버킷에 있는 모든 이미지의 URL 가져오기
def get_all_image_urls_from_bucket(bucket_name):
    try:
        # 버킷 조회
        bucket = storage_client.get_bucket(bucket_name)
        # 버킷 내의 모든 객체(Blob) 조회
        blobs = bucket.list_blobs()
        # 이미지 파일 확장자 리스트
        image_extensions = [".jpg", ".jpeg", ".png"]

        # 이미지 URL 리스트 초기화
        image_urls = []

        # 각 객체의 이름을 사용하여 이미지 URL 생성
        for blob in blobs:
            if any(blob.name.lower().endswith(ext) for ext in image_extensions):
                image_url = f"gs://{bucket_name}/{blob.name}"
                image_urls.append(image_url)

        return image_urls

    except Exception as e:
        print("Failed to get image URLs from bucket:", str(e))
        return []

# 분석 결과에서 식물 이름 추출
def get_plant_name(result):
    data = json.loads(result)
    label = data.get('label')
    if label is not None:
        return label
    return None


def save_result(plant_name):
    with app.app_context():
        plant = Plant(plt_name=plant_name)
        db.session.add(plant)
        db.session.commit()


# 이미지 분석 함수
def analyze_image(image):
    # 이미지를 640x640 크기로 변환
    img = image.resize((640, 640))
    img = img.convert('RGB')

    # 이미지 분석
    results = model(img)

    # 분석 결과를 JSON 형태로 변환
    result = result_to_json(image_to_base64(img), results)

    # 식물 이름 추출
    plant_name = get_plant_name(result)

    # 결과를 DB에 저장
    save_result(plant_name)

    return result

# 버킷에 있는 모든 이미지 분석
def analyze_all_images_in_bucket(bucket_name):

    # 버킷에 있는 모든 이미지의 URL 가져오기
    image_urls = get_all_image_urls_from_bucket(bucket_name)
    # 이미지 분석 및 처리
    for image_url in image_urls:

        # 이미지 다운로드
        image = download_image_from_storage(image_url)
        if image is not None:
            # 이미지 분석
            result = analyze_image(image)
            print(f"Analysis Result: {json.loads(result)['label']}")
            print("--------------------------")




# 이미지 다운로드 함수
def download_image_from_storage(image_url):
    try:
        # 이미지 URL에서 버킷 이름 추출
        bucket_name = image_url.split("//")[1].split("/")[0]

        # 버킷에서 이미지 파일 다운로드
        bucket = storage_client.get_bucket(bucket_name)
        image_blob = bucket.blob(image_url.split(bucket_name + "/")[1])
        image_data = image_blob.download_as_bytes()

        # 이미지를 PIL 객체로 변환
        image = Image.open(BytesIO(image_data))

        return image

    except Exception as e:
        print("Failed to download image from storage:", str(e))
        return None


# 버킷에 있는 모든 이미지 분석
analyze_all_images_in_bucket(bucket_name)


@app.route('/', methods=['GET'])
def index():

    # 버킷에 있는 모든 이미지 URL 가져오기
    image_urls = get_all_image_urls_from_bucket(bucket_name)

    return render_template('test.html', image_urls=image_urls)

