import os
import json
import openai
import cv2
import pytesseract


import requests
from PIL import Image
from io import BytesIO
import numpy as np

class Classifier:
    def __init__(self):
        token_path = 'tokens.json'
        if not os.path.isfile(token_path):
            raise Exception(f"{token_path} not found!")
        with open(token_path) as f:
            tokens = json.load(f)
            openai.organization = tokens['org']
            openai.api_key = tokens['key']

    def classify_text(self, message):
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system",
                 "content": "You are a content moderation system trained to detect potential scams in CS:GO trades and other forms of abuse such as physical threats, sexually violent content, or suicidal content. A message may be considered a scam if it suggests trading outside the official platform, asks for login credentials, or directs users to a third-party website. A message may be considered a physical threat or sexually violent content if it involves explicit or implicit threats or violent language of a sexual nature. A message may be considered suicidal content if it expresses thoughts of suicide or self-harm. Classify each input with the appropriate category, followed by the reason."},
                {"role": "user", "content": f"Is the following message a potential scam, physical threat or sexually violent content, or suicidal content, and if so why? Please make sure to start your response with the appropriate category (Scam, Physical Threat or Sexual Violence, Suicidal Content) and a period followed by the reason. Message: {message} "}
            ]
        )

        output = response['choices'][0]['message']['content']
        print(output)

        if output.startswith("Scam."):
            return "Scam", output[len("Scam."):].strip()
        elif output.startswith("Physical Threat or Sexual Violence."):
            return "Physical Threat or Sexual Violence", output[len("Physical Threat or Sexual Violence."):].strip()
        elif output.startswith("Suicidal Content."):
            return "Suicidal Content", output[len("Suicidal Content."):].strip()
        else:
            return "Not a Scam or Abuse", None

    # Add any additional preprocessing steps

    @staticmethod
    def preprocess_image(image_url):
        response = requests.get(image_url)
        img = Image.open(BytesIO(response.content))
        img_array = np.array(img)

        if len(img_array.shape) == 3:  # If the image has a third dimension (channels)
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        # Else, the image is already grayscale, no need for conversion

        # Thresholding
        threshold_img = cv2.threshold(img_array, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

        return threshold_img

    def classify_image(self, image_url):
        preprocessed_image = self.preprocess_image(image_url)
        custom_config = r'--oem 3 --psm 6'
        text = pytesseract.image_to_string(preprocessed_image, config=custom_config)
        text = text.replace("\n", " ")
        output = self.classify_text(text)
        return output, text
