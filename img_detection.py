import os
from PIL import Image
import io
from io import BytesIO
import base64
import json
import ultralytics

#from conda_token.repo_config import validate_token
from google.cloud import storage
import torch
from db_models import Plant, db, User
from dotenv import load_dotenv
from flask import Flask, request, render_template, jsonify, redirect, url_for
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity


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
storage_client = storage.Client.from_service_account_json('garden-genie-key.json')

# 버킷 이름 설정
bucket_name = 'garden_genie_image'

# 모델 로드
model_path = 'new_best.pt'
model = torch.hub.load('ultralytics/yolov5:v7.0', 'custom', path=model_path, force_reload=True)

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
        result_dict = {"image": image, "name": "No object detected"}
    else:
        result_dict = {"image": image, "name": ""}
        for result in results.xyxy[0]:
            label = class_names[int(result[5])]
            if label not in unique_labels:
                labels.append(label)
                unique_labels.add(label)
        if labels:
            result_dict["name"] = labels[0]
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
    name = data.get('name')
    if name is None:
        return "none"
    return name

def save_result(plant_name, plt_img, user_id):
    user = User.query.filter_by(user_id=user_id).first()
    if user is None:
        return "Invalid user_id"

    plant = Plant(plt_name=plant_name, plt_img=plt_img, user_id=user_id)
    db.session.add(plant)
    db.session.commit()
    return "Plant information saved successfully"


@app.route('/analyze', methods=['POST'])
@jwt_required()
def analyze_image():
    user_id = get_jwt_identity()
    image_url = request.json.get('image_url')
    plt_img = request.json.get('plt_img', '')

    # 이미지 다운로드
    image = download_image_from_storage(image_url)
    if image is not None:
        # 이미지를 640x640 크기로 변환
        resized_image = image.resize((640, 640))
        resized_image = resized_image.convert('RGB')

        # 이미지 분석
        results = model(resized_image)

        # 분석 결과를 JSON 형태로 변환
        result = result_to_json(image_to_base64(resized_image), results)

        # 식물 이름 추출
        plant_name = get_plant_name(result)
        print(f"Plant Name: {plant_name} (User ID: {user_id})")

        # 결과 저장
        save_result(plant_name=plant_name, plt_img=plt_img, user_id=user_id)

        response = {
            "message": "Image analyzed and result saved successfully",
            "plant_name": plant_name,
            "user_id": user_id
        }

        return jsonify(response), 200

### html ###

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # analyze 버튼 클릭 시 분석 결과 표시
        image_url = request.form.get('image_url')
        # 이미지 분석 로직 수행

        user_id = get_jwt_identity()
        # 이미지 다운로드
        image = download_image_from_storage(image_url)
        if image is not None:
            # 이미지를 640x640 크기로 변환
            resized_image = image.resize((640, 640))
            resized_image = resized_image.convert('RGB')

            # 이미지 분석
            results = model(resized_image)

            # 분석 결과를 JSON 형태로 변환
            result = result_to_json(image_to_base64(resized_image), results)

            # 식물 이름 추출
            plant_name = get_plant_name(result)
            print(f"Plant Name: {plant_name} (User ID: {user_id})")

            # 식물 정보와 사용자 아이디를 저장하는 코드 작성
            if plant_name is not None:
                new_plant = Plant(plt_name=plant_name, plt_img=None, user_id=user_id)
                db.session.add(new_plant)
                db.session.commit()
                return redirect(url_for('result'))
            else:
                return {'message': 'Plant name is required'}, 400
        else:
            print("Plant name could not be determined.")
            return {'message': 'Failed to analyze image'}, 400

    # GET 요청일 때 이미지 URL 목록 표시
    image_urls = get_all_image_urls_from_bucket(bucket_name)
    return render_template('index.html', image_urls=image_urls)


@app.route('/result')
def result():
    return render_template('result.html')


if __name__ == '__main__':
    app.run(debug=True)
