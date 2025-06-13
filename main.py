from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, Form, WebSocket
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
import re
import asyncio
import json

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

# WebSocket bağlantılarını tutacak set
active_connections = set()

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

class TextRequest(BaseModel):
    text: str
    language: str

class QARequest(BaseModel):
    text: str
    question: str

@app.post("/qa/")
async def question_answering(request: QARequest):
    prompt = f"""Aşağıdaki metne göre şu soruyu yanıtla:

Metin:
{request.text[:3000]}

Soru:
{request.question}
"""

    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Kullanıcının sorusunu sadece verilen metne göre cevaplayan bir asistansın."},
            {"role": "user", "content": prompt}
        ]
    )
    return {"answer": response.choices[0].message.content}

@app.post("/summarize/")
async def summarize_text(request: TextRequest):
    try:
        summary = summarize_with_gpt(request.text, request.language)
        return {"summary": summary}
    except Exception as e:
        return {"error": str(e)}

@app.websocket("/ws/progress")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.add(websocket)
    try:
        while True:
            # Bağlantıyı açık tut
            await websocket.receive_text()
    except:
        active_connections.remove(websocket)

async def broadcast_progress(progress: int, status: str):
    """Tüm aktif WebSocket bağlantılarına ilerleme durumunu gönder"""
    for connection in active_connections:
        try:
            await connection.send_json({
                "progress": progress,
                "status": status
            })
        except:
            active_connections.remove(connection)

@app.post("/analyze/")
async def analyze_youtube_video(url: str = Form(...)):
    try:
        video_id = str(uuid.uuid4())
        audio_path = Path(AUDIO_DIR) / f"{video_id}.m4a"

        await broadcast_progress(10, "Video indiriliyor...")
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

        await broadcast_progress(30, "Ses dosyası transkript ediliyor...")
        whisper_result = model.transcribe(str(audio_path), language="tr")
        text = whisper_result["text"]
        language = whisper_result["language"]

        await broadcast_progress(50, "Duygu analizi yapılıyor...")
        sentiment = sentiment_pipeline(text[:512])[0]
        sentiment_label = sentiment["label"]
        sentiment_score = sentiment["score"]

        await broadcast_progress(70, "Metin özetleniyor...")
        final_summary = summarize_with_gpt_and_sentiment(text, sentiment_label, sentiment_score)

        await broadcast_progress(90, "Video analizi tamamlanıyor...")
        video_type = "Podcast" if len(re.findall(r"\\b(sen|ben|biz|siz)\\b", text.lower())) > 10 else "Tek Anlatıcı"
        tone = "Tartışmalı" if "kadın" in text.lower() and "erkek" in text.lower() else "Nötr"
        participants = 2 if "sen" in text.lower() and "ben" in text.lower() else 1
        title_prompt = f"Bu metin için kısa ve etkili bir başlık öner:\n{text[:1000]}"

        title_response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Sen bir başlık üreticisisin."},
                {"role": "user", "content": title_prompt}
            ]
        )
        title = title_response.choices[0].message.content

        try:
            os.remove(audio_path)
        except:
            pass

        await broadcast_progress(100, "İşlem tamamlandı!")
        
        return {
            "transcript": text,
            "summary": final_summary,
            "sentiment_label": sentiment_label,
            "sentiment_score": sentiment_score,
            "video_type": video_type,
            "tone": tone,
            "participants": participants,
            "title": title.strip()
        }

    except Exception as e:
        await broadcast_progress(0, f"Hata oluştu: {str(e)}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
