from PIL import Image
from io import BytesIO
import base64
import json
from google.cloud import storage
import torch
from db_models import Plant, db
from flask import Flask, request, render_template, jsonify

app = Flask(__name__)

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
    unique_labels = set() # 레이블 중복 제거
    if len(results.xyxy[0]) == 0:
        result_dict = {"image": image, "results": [{"label": "No object detected"}]}
    else:
        result_dict = {"image": image, "results": []}
        for result in results.xyxy[0]:
            label = class_names[int(result[5])]
            if label not in unique_labels:
                result_dict["results"].append({"label": label})
                unique_labels.add(label)
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

# 이미지 분석 함수
def process_image(image):
    # 이미지를 640x640 크기로 변환
    img = image.resize((640, 640))
    img = img.convert('RGB')

    # 이미지 분석
    results = model(img)
    results.print()

    # 분석 결과를 JSON 형태로 변환
    result = result_to_json(image_to_base64(img), results)

# 버킷에 있는 모든 이미지 분석
def analyze_all_images_in_bucket(bucket_name):

    # 버킷에 있는 모든 이미지의 URL 가져오기
    image_urls = get_all_image_urls_from_bucket(bucket_name)

    # 이미지 분석 및 처리
    for image_url in image_urls:
        # 이미지 다운로드
        image = download_image_from_storage(image_url)
        if image is not None:
            result = process_image(image)
            print(f"Image URL: {image_url}")
            print(f"Analysis Result: {result}")
            print("---")

# 이미지 다운로드 함수
def download_image_from_storage(image_url):
    try:
        # 이미지 URL에서 버킷 이름 추출
        bucket_name = image_url.split("//")[1].split("/")[0]

        # 버킷에서 이미지 파일 다운로드
        bucket = storage_client.get_bucket(bucket_name)
        image_blob = bucket.blob(image_url.split(bucket_name + "/")[1])
        image_data = image_blob.download_as_bytes()
        image = Image.open(BytesIO(image_data))

        return image

    except Exception as e:
        print("Failed to download image from storage:", str(e))
        return None


# 버킷에 있는 모든 이미지 분석
analyze_all_images_in_bucket(bucket_name)

def get_plant_name(result):
    # 분석 결과에서 식물 이름 추출
    data = json.loads(result)
    if "results" in data:
        results = data["results"]
        if results:
            return results[0]["label"]
    return "Unknown"

def save_result(plant_name, image_url):
    pass
    # # 결과를 DB에 저장
    # plant = Plant(plt_name=plant_name, plt_img=image_url)
    # db.session.add(plant)
    # db.session.commit()

@app.route('/analyze', methods=['POST'])
def analyze_image():
    # 이미지 URL 받기
    if 'image_url' not in request.args:
        return jsonify({"error": "No image URL found in request."}), 400
    image_url = request.args['image_url']

    # 이미지 다운로드
    image = download_image_from_storage(image_url)
    if image is None:
        return jsonify({"error": "Failed to download image."}), 400

    # 이미지를 640x640 크기로 변환
    img = image.resize((640, 640))
    img = img.convert('RGB')

    # 이미지 분석
    results = model(img)
    results.print()

    # 분석 결과를 JSON 형태로 변환
    result = result_to_json(image_to_base64(img), results)

    # # 결과를 DB에 저장
    # plant_name = get_plant_name(result)
    # save_result(plant_name, image_url)

    return result

@app.route('/', methods=['GET'])
def index():

    # 버킷에 있는 모든 이미지 URL 가져오기
    image_urls = get_all_image_urls_from_bucket(bucket_name)

    # # DB에서 이미지 URL 가져오기
    # plants = Plant.query.all()
    # image_urls = [plant.plt_img for plant in plants]

    return render_template('test.html', image_urls=image_urls)

