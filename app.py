from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_socketio import SocketIO, emit
import os
import requests
import time
import eventlet

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
socketio = SocketIO(app)

REV_AI_API_KEY = 'your_rev_ai_api_key'  # Replace with your actual API key

def upload_to_rev(file_path):
    headers = {
        'Authorization': f'Bearer {REV_AI_API_KEY}'
    }
    files = {'media': open(file_path, 'rb')}
    response = requests.post('https://api.rev.ai/speechtotext/v1/jobs', headers=headers, files=files)
    
    # Debugging output
    print("Upload Response Status Code:", response.status_code)
    print("Upload Response Content:", response.content)

    if response.status_code == 201:  # HTTP status code for created
        return response.json().get('id')
    else:
        print("Error uploading file:", response.content)
        return None

def get_job_status(job_id):
    headers = {'Authorization': f'Bearer {REV_AI_API_KEY}'}
    response = requests.get(f'https://api.rev.ai/speechtotext/v1/jobs/{job_id}', headers=headers)
    
    if response.status_code == 200:
        return response.json().get('status')
    else:
        print("Error fetching job status:", response.content)
        return None

def get_transcript(job_id):
    headers = {'Authorization': f'Bearer {REV_AI_API_KEY}'}
    response = requests.get(f'https://api.rev.ai/speechtotext/v1/jobs/{job_id}/transcript', headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print("Error fetching transcript:", response.content)
        return None

def poll_for_transcript(job_id, max_retries=10, delay=5):
    for _ in range(max_retries):
        status = get_job_status(job_id)
        if status == 'transcribed':
            return get_transcript(job_id)
        elif status in ['failed', 'cancelled']:
            print(f"Job failed or was cancelled. Status: {status}")
            return None
        time.sleep(delay)  # Wait before retrying
    print("Exceeded maximum retries")
    return None

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['audio_file']
        if file:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)
            job_id = upload_to_rev(file_path)
            if job_id:
                return redirect(url_for('transcription', job_id=job_id))
            else:
                return "Error uploading file to Rev.ai", 500
    return render_template('index.html')

@app.route('/transcription/<job_id>')
def transcription(job_id):
    transcript = poll_for_transcript(job_id)
    if transcript:
        return render_template('transcription.html', transcript=transcript)
    else:
        return "Error fetching transcription or job failed", 500

# Commented out for now
# async def realtime_speech_to_text(audio_gen):
#     async with websockets.connect(
#             'wss://api.rev.ai/speechtotext/v1/stream',
#             extra_headers={"Authorization": f"Bearer {REV_AI_API_KEY}"}
#         ) as websocket:
#         
#         async for audio_chunk in audio_gen:
#             await websocket.send(audio_chunk)
# 
#         while True:
#             result = await websocket.recv()
#             socketio.emit('transcription_result', result)

# Commented out for now
# @socketio.on('audio_chunk')
# def handle_audio_chunk(audio_chunk):
#     asyncio.run(realtime_speech_to_text(audio_chunk))

if __name__ == '__main__':
    eventlet.wsgi.server(eventlet.listen(('0.0.0.0', 5000)), app)
