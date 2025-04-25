from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile
import uvicorn
import subprocess
from pathlib import Path
import os
import whisper
from pydantic import BaseModel
import openai
import hashlib
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Gerekirse frontend domaini ile sınırla
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"]
)

UPLOAD_DIR = "uploads"
AUDIO_DIR = "audio"
TRANSCRIPTION_DIR = "transcriptions"
FFMPEG_PATH = r"C:\\ffmpeg-7.1.1-essentials_build\\ffmpeg-7.1.1-essentials_build\\bin\\ffmpeg.exe"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(TRANSCRIPTION_DIR, exist_ok=True)

model = whisper.load_model("medium")

# 🔁 GPT-3.5 özetleme modeli (API erişimi olan model)
openai.api_key = "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"

# Ön bellek (basit sözlük)
summary_cache = {}

def get_text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def summarize_with_gpt(text: str):
    text_hash = get_text_hash(text)
    if text_hash in summary_cache:
        return summary_cache[text_hash]

    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that summarizes texts."},
            {"role": "user", "content": f"Please summarize this text:\n\n{text}"}
        ],
        temperature=0.5,
    )
    summary = response.choices[0].message.content
    summary_cache[text_hash] = summary
    return summary

@app.post("/upload/")
async def upload_video(file: UploadFile = File(...)):
    file_path = Path(UPLOAD_DIR) / file.filename
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
    return {"message": "Video yüklendi", "filename": file.filename}

@app.post("/extract-audio/")
async def extract_audio(filename: str):
    try:
        video_path = Path(UPLOAD_DIR) / filename
        audio_path = Path(AUDIO_DIR) / f"{Path(filename).stem}.wav"

        if not video_path.exists():
            return {"error": "Video dosyası bulunamadı.", "filename": filename}

        if audio_path.exists():
            return {"message": "Ses dosyası zaten mevcut.", "audio_file": str(audio_path)}

        command = [FFMPEG_PATH, "-i", str(video_path), "-q:a", "0", "-map", "a", str(audio_path)]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode != 0:
            return {"error": "FFmpeg çalıştırılırken hata oluştu.", "details": result.stderr}

        if not audio_path.exists():
            return {"error": "Ses dosyası oluşturulamadı!", "filename": filename}

        return {"message": "Ses çıkarıldı", "audio_file": str(audio_path)}

    except Exception as e:
        return {"error": "Bilinmeyen bir hata oluştu.", "details": str(e)}

@app.post("/transcribe-audio/")
async def transcribe_audio(filename: str):
    try:
        audio_path = Path(AUDIO_DIR) / f"{Path(filename).stem}.wav"
        absolute_audio_path = audio_path.resolve(strict=False)

        try:
            with open(absolute_audio_path, "rb") as f:
                pass
        except FileNotFoundError:
            return {"error": "Ses dosyası bulunamadı.", "filename": filename}
        except PermissionError:
            return {"error": "Dosya erişim hatası.", "filename": filename}

        result = model.transcribe(str(absolute_audio_path), language="en")
        return {"message": "Transkripsiyon tamamlandı", "text": result["text"]}

    except Exception as e:
        return {"error": str(e)}

class TextRequest(BaseModel):
    text: str

@app.post("/summarize/")
async def summarize_text(request: TextRequest):
    try:
        summary = summarize_with_gpt(request.text)
        return {"summary": summary}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
