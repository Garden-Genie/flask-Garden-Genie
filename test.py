from io import BytesIO
import base64
import json
from PIL import Image
import torch
from flask import Flask, request, render_template, jsonify

app = Flask(__name__)

# 클래스 이름
class_names = ['Clusia', 'Fan-Palms', 'Lvicks plant', 'Pachira', 'Wind orchid', 'caladium',
               'carnation', 'creeping fig', 'croton', 'eucalyptus', 'freesia', 'geranium',
               'poinsettia', 'ribbon plant']


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

# 이미지 분석 API
@app.route('/analyze', methods=['POST'])
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
    return result


# if __name__ == '__main__':
#    app.run(debug=True, host='0.0.0.0', port=5000)

# 테스트 루트 페이지
@app.route('/')
def index():
    return render_template('test_img.html')


#if __name__ == '__main__':
#    app.run()
