from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, Form
import uvicorn
import subprocess
from pathlib import Path
import os
import whisper
from pydantic import BaseModel
import openai
import hashlib
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp
import uuid
import shutil
from transformers import pipeline
from fastapi.responses import JSONResponse

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

UPLOAD_DIR = "uploads"
AUDIO_DIR = "audio"
TRANSCRIPTION_DIR = "transcriptions"
FFMPEG_PATH = "ffmpeg"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(TRANSCRIPTION_DIR, exist_ok=True)

model = whisper.load_model("base")
sentiment_pipeline = pipeline("sentiment-analysis", model="nlptown/bert-base-multilingual-uncased-sentiment")

summary_cache = {}

def get_text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def summarize_with_gpt(text: str, language: str):
    text_hash = get_text_hash(text)
    if text_hash in summary_cache:
        return summary_cache[text_hash]

    if language == "tr":
        system_prompt = "Sen yardımcı bir asistansın. Görevin verilen Türkçe metni özetlemek."
        user_prompt = f"Lütfen bu metni özetle:\n\n{text}"
    else:
        system_prompt = "You are a helpful assistant that summarizes texts."
        user_prompt = f"Please summarize this text:\n\n{text}"

    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.5,
    )
    summary = response.choices[0].message.content
    summary_cache[text_hash] = summary
    return summary

def summarize_with_gpt_and_sentiment(text: str, sentiment_label: str, sentiment_score: float):
    system_prompt = (
        "Sen metinleri analiz eden bir yapay zekasın. Sana verilen metni önce özetle. Ardından verilen duygu analiz skoruna göre "
        "metnin duygusal tonunu değerlendir."
    )
    user_prompt = f"""
Metin:
{text}

Duygu analizi sonucu:
{sentiment_label} (Skor: {sentiment_score:.2f})

Lütfen önce metni kısa şekilde özetle. Ardından duygu skoruna göre duygusal ton hakkında yorum yap:
"""

    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.5,
    )
    return response.choices[0].message.content

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

        result = model.transcribe(str(absolute_audio_path))
        text = result["text"]
        language = result["language"]

        return {
            "message": "Transkripsiyon tamamlandı",
            "text": text,
            "language": language
        }

    except Exception as e:
        return {"error": str(e)}

class TextRequest(BaseModel):
    text: str
    language: str

@app.post("/summarize/")
async def summarize_text(request: TextRequest):
    try:
        summary = summarize_with_gpt(request.text, request.language)
        return {"summary": summary}
    except Exception as e:
        return {"error": str(e)}

@app.post("/analyze/")
async def analyze_youtube_video(url: str = Form(...)):
    try:
        video_id = str(uuid.uuid4())
        audio_path = Path(AUDIO_DIR) / f"{video_id}.m4a"

        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio/best',
            'outtmpl': str(audio_path),
            'quiet': True,
            'noplaylist': True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        if not audio_path.exists():
            return JSONResponse(content={"error": "Ses dosyası indirilemedi"}, status_code=400)

        whisper_result = model.transcribe(str(audio_path), language="tr")
        text = whisper_result["text"]
        language = whisper_result["language"]

        sentiment = sentiment_pipeline(text[:512])[0]
        sentiment_label = sentiment["label"]
        sentiment_score = sentiment["score"]

        final_summary = summarize_with_gpt_and_sentiment(text, sentiment_label, sentiment_score)

        try:
            os.remove(audio_path)
        except:
            pass

        return {
            "transcript": text,
            "summary": final_summary,
            "sentiment_label": sentiment_label,
            "sentiment_score": sentiment_score
        }

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
