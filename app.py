from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO
import os
import requests
import time
from rev_ai import apiclient 
import eventlet
from dotenv import load_dotenv


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
socketio = SocketIO(app)

load_dotenv()

# Retrieve the API key from the environment variables
REV_AI_API_KEY = os.getenv('REV_AI_API_KEY')

if not REV_AI_API_KEY:
    raise ValueError('API key is not set in environment variables')

# Initialize the RevAiAPIClient with the retrieved API key
client = apiclient.RevAiAPIClient(REV_AI_API_KEY)


def transcribe_audio(file_path):
    # Submit the MP3 file for transcription
    job = client.submit_job_local_file(file_path)

    # Check the job status
    job_details = client.get_job_details(job.id)
    while job_details.status == "in_progress":
        time.sleep(60)  # Poll every 60 seconds
        job_details = client.get_job_details(job.id)
        print("Job status:", job_details.status)

    # Once the job is complete, retrieve the transcript
    if job_details.status == "transcribed":
        transcript_text = client.get_transcript_text(job.id)
        return transcript_text
    else:
        print(f"Job failed or was cancelled. Status: {job_details.status}")
        return None

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files.get('audio_file')
        if file:
            # Save the uploaded audio file
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'recording.mp3')
            file.save(file_path)
            
            # Transcribe the audio file
            transcript_text = transcribe_audio(file_path)
            
            if transcript_text:
                # Redirect to a page displaying the transcription result
                return render_template('transcription.html', transcript=transcript_text)
            else:
                return "Error: Transcription failed or job was cancelled", 500
    return render_template('index.html')

# Route for the upload page
@app.route('/upload')
def upload():
    return render_template('upload.html')

# Route for the live transcription page
@app.route('/record')
def record():
    return render_template('record.html')

if __name__ == '__main__':
    eventlet.wsgi.server(eventlet.listen(('0.0.0.0', 5000)), app)