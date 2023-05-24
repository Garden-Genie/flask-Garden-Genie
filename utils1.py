from io import BytesIO
import base64
import json


class_names = ['Clusia', 'Fan-Palms', 'Lvicks plant', 'Pachira', 'Wind orchid', 'caladium',
               'carnation', 'creeping fig', 'croton', 'eucalyptus', 'freesia', 'geranium',
               'poinsettia', 'ribbon plant']

def image_to_base64(image):
    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue())
    return img_str.decode('utf-8')

def result_to_json(image, results):
    unique_labels = set()
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

