import os
import json
import pandas as pd
import random
import requests
from flask import Flask, request, jsonify, render_template
from ultralytics import YOLO
import openai

app = Flask(__name__)

# OpenAI API key
openai.api_key = "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"

# Load YOLO model
yolo_model = YOLO('20241002_input2400_batch128/train/weights/best.pt')

# Function to get a random Seoul region
def get_random_seoul_region():
    latitude_min, latitude_max = 37.4133, 37.7151
    longitude_min, longitude_max = 126.7341, 127.1830
    headers = {'Authorization': 'KakaoAK 88dde6ce7fafb4116e0f7f2342d53557'}

    while True:
        latitude = random.uniform(latitude_min, latitude_max)
        longitude = random.uniform(longitude_min, longitude_max)
        url = f'https://dapi.kakao.com/v2/local/geo/coord2regioncode.json?x={longitude}&y={latitude}'
        response = requests.get(url, headers=headers)
        data = response.json()
        if data['documents'] and data['documents'][0]['region_1depth_name'] == "서울특별시":
            return data['documents'][0]['region_2depth_name'], data['documents'] and data['documents'][0]["address_name"]

# Function to process and generate recycling guidelines
def generate_recycling_guidelines(predicted_class, gu, full_location):
    # Load guidelines from CSV files
    df = pd.read_csv("test.csv")
    location_info = df[df['location'] == f"{gu}"]['guideline'].to_list()[0]

    df2 = pd.read_csv("guideline.csv")
    recycling_info = df2[df2[' 품목'] == f"{predicted_class}"]['가이드'].to_list()[0]

    # Generate prompt for OpenAI API
    prompt = f"""
        다음 품목의 재활용 가이드를 아래 형식에 맞춰 명확한 정보를 제공해 주세요.
        - 품목: {predicted_class.split(sep='_')[1]}
        - '{predicted_class.split(sep='_')[1]}' 품목의 분리배출 가이드라인: {recycling_info}
        - '{full_location}' 지역의 분리배출 가이드라인: {location_info}

        아래의 항목에 대해 적절한 답변을 제공해 주세요. 답변 형식은 아래와 같습니다. 적절한 답변이 없으면 없다고 해주세요.
        각 항목별 답변은 중복되지 않도록 해주세요. 아래 항목 별 답변 간 반드시 '\n\n' 해주세요. 답변 내 항목도 반드시 '\n\n'로 구분해주세요. :

        ● **품목**: {predicted_class.split(sep='_')[1]} \n\n
        ● **현재 지역**: {full_location} \n\n
        ● **분리 배출 방법**: 이 품목을 올바르게 배출하는 방법을 단계별로 구체적으로 설명해 주세요. \n\n
        ● **지역별 정보**: 해당 지역의 해당 품목의 분리배출 정보를 시간, 날짜를 포함하여 자세하게 알려주세요. \n\n
        ● **추가 정보**: 이 품목의 관련하여 추가사항을 알려주세요. 전화번호나 해당 구청의 url을 안내해주세요. \n\n
    """

    # Get response from OpenAI API
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message['content']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/send_image', methods=['POST'])
@app.route('/select_item', methods=['POST'])
def send_image():
    uploaded_file = request.files.get("image")

    # Get a random Seoul region
    gu, full_location = get_random_seoul_region()
    
    # Step 1: Check if image is uploaded
    if uploaded_file and uploaded_file.filename.endswith((".jpg", ".png")):
        # Create uploads directory if it doesn't exist
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        image_path = os.path.join(upload_dir, uploaded_file.filename)
        uploaded_file.save(image_path)

        # Step 2: Run YOLO model on the uploaded image
        results = yolo_model(image_path)

        # Step 3: Check if YOLO predicted an object
        if results[0].boxes:
            predicted_class = results[0].names[int(results[0].boxes.cls[0])]
        else:
            predicted_class = "알 수 없는 품목"
    else:
        # If no image is uploaded, process the selected item
        select_item = request.get_json()
        temp_class = select_item.get('selected_item', None)

        # Error handling for missing user selection
        if temp_class is None:
            return jsonify({"response": "품목을 선택하지 않으셨습니다. 다시 시도해 주세요."})

        # Retrieve selected item from JSON file
        with open("items.json", "r", encoding="utf-8") as file:
            item_list = json.load(file)
            predicted_class = item_list[temp_class]

    # Generate recycling guidelines
    answer = generate_recycling_guidelines(predicted_class, gu, full_location)
    return jsonify({"response": answer})

if __name__ == "__main__":
    app.run(port=5000)
