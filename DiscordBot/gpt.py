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
                 "content": "You are a content moderation system trained to detect potential scams in CS:GO trades. A message may be considered a scam if it suggests trading outside the official platform, asks for login credentials, or directs users to a third-party website. Classify each input as either 'Scam' or 'Not a Scam'."},
                {"role": "user", "content": f"Is the following message a potential scam, and if so why? Please make sure to start your response with either 'Scam.' or 'Not a scam.' followed by the reason. Message: {message} "}
            ]
        )

        output = response['choices'][0]['message']['content']
        # output = "Scam. The message directs users to a third-party website, which is a common tactic used by scammers to steal login credentials or trick users into downloading malware."
        if output.startswith("Scam."):
            return "Scam", output[len("Scam."):].strip()
        else:
            return "Not Scam", "N/A"

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
