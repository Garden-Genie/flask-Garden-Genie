import os
import base64
import json
from PIL import Image
import torch
from io import BytesIO
from google.cloud import storage
from db_models import Plant, db, User
from dotenv import load_dotenv
from flask import Flask, render_template
from flask import current_app

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
        result_dict = {"image": image, "name": "No object detected"}  # "label"을 "name"으로 변경
    else:
        result_dict = {"image": image, "name": ""}
        for result in results.xyxy[0]:
            label = class_names[int(result[5])]
            if label not in unique_labels:
                labels.append(label)
                unique_labels.add(label)
        if labels:
            result_dict["name"] = labels[0]  # "label"을 "name"으로 변경
    return json.dumps(result_dict)

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

# 분석 결과에서 식물 이름 추출
def get_plant_name(result):
    data = json.loads(result)
    name = data.get('name')  # "label"을 "name"으로 변경
    if name is not None:
        return name
    return None

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
    print("Plant Name:", plant_name)

    return plant_name

# 버킷에 있는 모든 이미지 분석
def analyze_all_images_in_bucket(bucket_name):
    # 버킷에 있는 모든 이미지의 URL 가져오기
    image_urls = get_all_image_urls_from_bucket(bucket_name)

    # 사용자 ID 가져오기
    with app.app_context():
        user_ids = [str(user.user_id) for user in User.query.all()]  # 사용자 ID를 문자열로 변환

    # 이미지 분석 및 처리
    for i, image_url in enumerate(image_urls):
        # 이미지 다운로드
        image = download_image_from_storage(image_url)
        if image is not None:
            # 이미지 분석
            plant_name = analyze_image(image)

            # 사용자별로 결과 저장 및 출력
            if i < len(user_ids):
                user_id = user_ids[i]
            else:
                user_id = "No object detected"

            if plant_name is None:
                plant_name = "No object detected"

            save_result(plant_name, image_url, user_id)
            print(f"Analysis Result for User {user_id}: {plant_name}")
            print("-------------------------------------------")

def save_result(plant_name, image_url, user_id):
    with app.app_context():
        user = User.query.filter_by(user_id=user_id).first()
        if user:
            plant = Plant(plt_name=plant_name, plt_img=image_url, user_id=user_id)
            db.session.add(plant)
            db.session.commit()
        else:
            print(f"User ID '{user_id}' does not exist in the database.")


# 버킷에 있는 모든 이미지 분석
with app.app_context():
    analyze_all_images_in_bucket(bucket_name)

@app.route('/', methods=['GET'])
def index():

    # 버킷에 있는 모든 이미지 URL 가져오기
    image_urls = get_all_image_urls_from_bucket(bucket_name)
    return render_template('test.html', image_urls=image_urls)
