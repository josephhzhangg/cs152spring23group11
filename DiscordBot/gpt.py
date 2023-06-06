import os
import json
import openai


class Classifier:
    def __init__(self):
        token_path = 'tokens.json'
        if not os.path.isfile(token_path):
            raise Exception(f"{token_path} not found!")
        with open(token_path) as f:
            tokens = json.load(f)
            openai.organization = tokens['org']
            openai.api_key = tokens['key']

    def classify(self, message):
        # response = openai.ChatCompletion.create(
        #     model="gpt-3.5-turbo",
        #     messages=[
        #         {"role": "system",
        #          "content": "You are a content moderation system trained to detect potential scams in CS:GO trades. A message may be considered a scam if it suggests trading outside the official platform, asks for login credentials, or directs users to a third-party website. Classify each input as either 'Scam' or 'Not a Scam'."},
        #         {"role": "user", "content": f"Is the following message a potential scam, and if so why? Please make sure to start your response with either 'Scam.' or 'Not a scam.' followed by the reason. Message: {message} "}
        #     ]
        # )
        #
        # output = response['choices'][0]['message']['content']
        output = "Scam. The message directs users to a third-party website, which is a common tactic used by scammers to steal login credentials or trick users into downloading malware."
        if output.startswith("Scam."):
            return "Scam", output[len("Scam."):].strip()
        else:
            return "Not Scam", "N/A"
