from flask import Flask, request, jsonify
from openai import OpenAI
import json
import re

app = Flask(__name__)


with open('config.json') as config_file:
    config = json.load(config_file)
    PAT = config['PAT']
    USER_ID = config['USER_ID']
    APP_ID = config['APP_ID']
    MODEL_ID = config['MODEL_ID']
    MODEL_VERSION_ID = config['MODEL_VERSION_ID'] 

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
    RAW_TEXT = f'Behave you are a priority schedular app, set a priority of high or medium or low for the task,{RAW_TEXT}. Also, break the task in to 2 or 3 steps to make it easier'
    client = OpenAI(
        api_key="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"
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
