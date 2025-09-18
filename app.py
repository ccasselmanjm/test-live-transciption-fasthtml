# app.py
import tempfile
import subprocess
import whisper
from fasthtml.common import *

# Load whisper model (tiny/base/small/medium/large)
model = whisper.load_model("base")

app, rt = fast_app()

def safe_transcribe(path: str) -> str:
    """Convert input file to WAV with ffmpeg before passing to Whisper."""
    with tempfile.NamedTemporaryFile(suffix=".wav") as wav:
        cmd = [
            "ffmpeg", "-y", "-i", path,
            "-ar", "16000", "-ac", "1", "-f", "wav", wav.name
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            result = model.transcribe(wav.name, fp16=False, language="en")
            return result["text"].strip()
        except subprocess.CalledProcessError:
            return ""

@rt("/")
def index():
    return Titled("🎙️ Live Transcription Demo",
        Div(
            Button("🎙️ Start Recording", id="record-btn"),
            Button("🧹 Clear Transcript", id="clear-btn", style="margin-left:10px;"),
            Pre(id="transcript", style="margin-top:20px; font-size:1.2em; white-space:pre-wrap;")
        ),
        Script("""
        let mediaRecorder;
        let currentStream;
        let transcriptDiv = document.getElementById("transcript");
        const btn = document.getElementById("record-btn");
        const clearBtn = document.getElementById("clear-btn");

        clearBtn.onclick = () => { transcriptDiv.textContent = ""; };

        async function startNewRecorder() {
            // Close any old stream
            if (currentStream) {
                currentStream.getTracks().forEach(track => track.stop());
            }

            currentStream = await navigator.mediaDevices.getUserMedia({ audio: true });

            // 🔊 AudioContext for silence detection
            const audioContext = new AudioContext();
            const source = audioContext.createMediaStreamSource(currentStream);
            const analyser = audioContext.createAnalyser();
            analyser.fftSize = 512;
            source.connect(analyser);
            const dataArray = new Uint8Array(analyser.fftSize);

            function detectSilence(threshold = 5, timeout = 2000) {
                let silenceStart = performance.now();
                let triggered = false;

                function loop() {
                    analyser.getByteTimeDomainData(dataArray);
                    let sum = 0;
                    for (let i = 0; i < dataArray.length; i++) {
                        let val = (dataArray[i] - 128) / 128;
                        sum += val * val;
                    }
                    let rms = Math.sqrt(sum / dataArray.length) * 100;

                    if (rms < threshold) {
                        if (!triggered && performance.now() - silenceStart > timeout) {
                            console.log("🤫 Pause detected, restarting recorder…");
                            triggered = true;
                            mediaRecorder.stop();
                            startNewRecorder(); // 🔄 restart automatically
                            return;
                        }
                    } else {
                        silenceStart = performance.now();
                        triggered = false;
                    }

                    requestAnimationFrame(loop);
                }
                loop();
            }

            // pick best format
            let mimeType;
            if (MediaRecorder.isTypeSupported("audio/ogg; codecs=opus")) {
                mimeType = "audio/ogg; codecs=opus";
            } else if (MediaRecorder.isTypeSupported("audio/webm; codecs=opus")) {
                mimeType = "audio/webm; codecs=opus";
            } else {
                mimeType = "";
            }

            mediaRecorder = new MediaRecorder(currentStream, { mimeType });

            mediaRecorder.ondataavailable = async (e) => {
                if (e.data && e.data.size > 8000) {  // smaller threshold since chunks are 2s
                    let ext = mimeType.includes("ogg") ? "ogg" : "webm";
                    const formData = new FormData();
                    formData.append("file", e.data, "chunk." + ext);

                    try {
                        const resp = await fetch("/stream", { method: "POST", body: formData });
                        const text = await resp.text();
                        if (text.trim().length > 0) {
                            transcriptDiv.textContent += text + " ";
                        }
                    } catch (err) {
                        console.error("Upload failed:", err);
                    }
                }
            };

            mediaRecorder.start(2000); // ✅ send every 2s
            detectSilence(5, 2000);    // silence = <2s
        }

        btn.onclick = async () => {
            if (!mediaRecorder || mediaRecorder.state === "inactive") {
                await startNewRecorder();
                btn.textContent = "⏹️ Stop Recording";
            } else {
                mediaRecorder.stop();
                if (currentStream) {
                    currentStream.getTracks().forEach(track => track.stop());
                }
                btn.textContent = "🎙️ Start Recording";
            }
        };
        """)
    )

@rt("/stream", methods=["POST"])
async def stream(req):
    form = await req.form()
    file = form["file"]

    data = file.file.read()
    if not data or len(data) < 8000:  # ~2s worth of compressed Opus
        return ""

    with tempfile.NamedTemporaryFile(delete=True, suffix=".ogg") as tmp:
        tmp.write(data)
        tmp.flush()
        try:
            return safe_transcribe(tmp.name)
        except Exception as e:
            print("⚠️ Skipping invalid/partial chunk:", e)
            return ""

serve()
