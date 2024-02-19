from flask import Flask, request, jsonify
from openai import OpenAI
import json
import re

app = Flask(__name__)


def decrypt_caesar(encrypted_text, shift):
    decrypted_text = ""
    for char in encrypted_text:
        if char == '#':
            decrypted_text += '-'
        elif char.isalpha():
            shifted_char = chr((ord(char.lower()) - ord('a') - shift) % 26 + ord('a'))
            if char.isupper():
                shifted_char = shifted_char.upper()
            decrypted_text += shifted_char
        else:
            decrypted_text += char
    return decrypted_text

with open('config.json') as config_file:
    config = json.load(config_file)
    API_KEY = decrypt_caesar(config['API_KEY'], 3)

step_re = re.compile(r'Step (\d+): (.*)')
num_re = re.compile(r'\d+')
step_clean_re = re.compile(r'Step \d+:')

def extract_steps_text(text):
    steps_matches = step_re.findall(text)
    return steps_matches

def clean_sort(text):
    steps = extract_steps_text(text)
    sorted_steps = sorted(steps, key=lambda x: int(num_re.search(x[0]).group()))
    cleaned_steps = [step_clean_re.sub('', step[1]) for step in sorted_steps]
    return cleaned_steps

def extract_priority(text):
    priority_match = re.search(r'Priority: (\w+)', text)
    if priority_match:
        priority = priority_match.group(1).capitalize()
        if priority in ["High", "Medium", "Low"]:
            return priority
    return "Low"


@app.route('/predict', methods=['POST'])
def predict_model_output():
    data = request.json
    RAW_TEXT = data['text']
    RAW_TEXT = f'Behave you are a priority schedular app, set a priority of high or medium or low for the task,{RAW_TEXT}. Also, break the task in to 2 or 3 steps to make it easier. They should be in the format of Step 1: Do something, Step 2: Do something else, etc. and the steps must be only about 4-5 words long'
    client = OpenAI(
        api_key=API_KEY
    )
    
    
    try:
        completion = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": f"Behave you are a priority schedular app, set a priority of high or medium or low for the task,{RAW_TEXT}. Also, break the task in to 2 or 3 steps to make it easier"}
        ]
        )

        text = completion.choices[0].message.content
        priority_task = extract_priority(text)
        task_breakdonw = clean_sort(text)
        response_data = {
            "priority": priority_task,
            "steps": task_breakdonw
        }
        return jsonify(response_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
