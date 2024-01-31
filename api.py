from flask import Flask, request, jsonify
from clarifai_grpc.channel.clarifai_channel import ClarifaiChannel
from clarifai_grpc.grpc.api import resources_pb2, service_pb2, service_pb2_grpc
from clarifai_grpc.grpc.api.status import status_code_pb2
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

def steps_extract(text):
    steps = re.findall(r'Step \d+: [^\n]+', text)
    return steps

def clean_sort(text):
    steps = steps_extract(text)
    sorted_steps = sorted(steps, key=lambda x: int(re.search(r'\d+', x).group()))
    cleaned_steps = [re.sub(r'Step \d+: ', '', step) for step in sorted_steps]
    return cleaned_steps

def extract_priority(text):
    first_sentence = text.split('.')[0]
    priorities = ["high", "medium", "low"]
    
    for priority in priorities:
        if priority in first_sentence.lower():
            print(priority)
            return priority.capitalize()
    
    return "Low"

@app.route('/predict', methods=['POST'])
def predict_model_output():
    data = request.json
    RAW_TEXT = data['text']
    RAW_TEXT = f'Behave you are a priority schedular app, set a priority of high or medium or low for the task,{RAW_TEXT}. Also, break the task in to 2 or 3 steps to make it easier'
    channel = ClarifaiChannel.get_grpc_channel()
    stub = service_pb2_grpc.V2Stub(channel)

    metadata = (('authorization', 'Key ' + PAT),)
    userDataObject = resources_pb2.UserAppIDSet(user_id=USER_ID, app_id=APP_ID)

    try:
        post_model_outputs_response = stub.PostModelOutputs(
            service_pb2.PostModelOutputsRequest(
                user_app_id=userDataObject,
                model_id=MODEL_ID,
                version_id=MODEL_VERSION_ID,
                inputs=[
                    resources_pb2.Input(
                        data=resources_pb2.Data(
                            text=resources_pb2.Text(
                                raw=RAW_TEXT
                            )
                        )
                    )
                ]
            ),
            metadata=metadata
        )
        if post_model_outputs_response.status.code != status_code_pb2.SUCCESS:
            print(post_model_outputs_response.status)
            raise Exception(f"Post model outputs failed, status: {post_model_outputs_response.status.description}")

        output = post_model_outputs_response.outputs[0]
        text = output.data.text.raw
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
