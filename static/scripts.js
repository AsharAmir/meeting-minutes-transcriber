const socket = io.connect('http://localhost:5000');
let mediaRecorder;

function startRecording() {
    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
            mediaRecorder = new MediaRecorder(stream);
            mediaRecorder.ondataavailable = function (e) {
                if (e.data.size > 0) {
                    socket.emit('start_audio_stream', e.data);
                }
            };
            mediaRecorder.start(250); // Send audio chunks every 250ms
        })
        .catch(err => console.error('Error capturing audio:', err));
}

function stopRecording() {
    if (mediaRecorder) {
        mediaRecorder.stop();
        socket.emit('stop_audio_stream');
    }
}

socket.on('transcript', function (data) {
    document.getElementById('transcription').textContent += data + '\n';
});
