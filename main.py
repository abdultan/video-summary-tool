from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, Form, WebSocket, Depends, HTTPException, status, Header, Request
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
import torch
import sqlite3
from passlib.context import CryptContext
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta

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
CACHE_DIR = "cache"
FFMPEG_PATH = "ffmpeg"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(TRANSCRIPTION_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

if torch.cuda.is_available():
    device = "cuda"
    print("GPU kullanılıyor!")
else:
    device = "cpu"
    print("CPU kullanılıyor!")

model = whisper.load_model("base", device=device)
sentiment_pipeline = pipeline("sentiment-analysis", model="nlptown/bert-base-multilingual-uncased-sentiment", device=0 if torch.cuda.is_available() else -1)

summary_cache = {}

# WebSocket bağlantılarını tutacak set
active_connections = set()

# Veritabanı bağlantısı ve kullanıcı tablosu
conn = sqlite3.connect('users.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL
)''')
c.execute('''CREATE TABLE IF NOT EXISTS summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    url TEXT NOT NULL,
    transcript TEXT,
    summary TEXT,
    sentiment_label TEXT,
    sentiment_score REAL,
    video_type TEXT,
    tone TEXT,
    participants INTEGER,
    title TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
)''')
conn.commit()

SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login/")

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def get_url_hash(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()

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
    title: str
    summary: str
    transcript: str
    question: str

class UserRegister(BaseModel):
    email: str
    password: str

@app.post("/qa/")
async def question_answering(request: QARequest):
    prompt = f"""Aşağıda bir YouTube videosunun başlığı, özeti ve transkripti var. Kullanıcıdan gelen her türlü soruya, elindeki tüm bilgilerle ve genel bilgiyle ChatGPT gibi yardımcı ol:

Başlık:
{request.title}

Özet:
{request.summary}

Transkript:
{request.transcript}

Soru:
{request.question}
"""
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Sen ChatGPT tarzında, video hakkında her türlü soruya yardımcı olan bir asistansın."},
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

def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Kimlik doğrulama başarısız.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    c.execute("SELECT id, email FROM users WHERE id = ?", (user_id,))
    user = c.fetchone()
    if user is None:
        raise credentials_exception
    return {"id": user[0], "email": user[1]}

@app.post("/analyze/")
async def analyze_youtube_video(
    request: Request,
    url: str = Form(...)
):
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token eksik veya geçersiz.")
    token = auth_header.split(" ")[1]
    user = get_current_user(token)
    try:
        url_hash = get_url_hash(url)
        cache_file_path = Path(CACHE_DIR) / f"{url_hash}.json"

        # Önbellekte var mı kontrol et
        if cache_file_path.exists():
            with open(cache_file_path, "r", encoding="utf-8") as f:
                cached_result = json.load(f)
            # Kullanıcının geçmişine ekle (varsa tekrar eklemez)
            c.execute("SELECT 1 FROM summaries WHERE user_id=? AND url=?", (user["id"], url))
            if not c.fetchone():
                c.execute("INSERT INTO summaries (user_id, url, transcript, summary, sentiment_label, sentiment_score, video_type, tone, participants, title) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (user["id"], url, cached_result["transcript"], cached_result["summary"], cached_result["sentiment_label"], cached_result["sentiment_score"], cached_result["video_type"], cached_result["tone"], cached_result["participants"], cached_result["title"]))
                conn.commit()
            return JSONResponse(content=cached_result, status_code=200)

        video_id = str(uuid.uuid4())
        audio_path = Path(AUDIO_DIR) / f"{video_id}.m4a"

        await broadcast_progress(10, "Video indiriliyor...")
        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio/best',
            'outtmpl': str(audio_path),
            'quiet': True,
            'noplaylist': True,
            'cookiefile': 'cookies.txt'
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
        
        result_to_cache = {
            "transcript": text,
            "summary": final_summary,
            "sentiment_label": sentiment_label,
            "sentiment_score": sentiment_score,
            "video_type": video_type,
            "tone": tone,
            "participants": participants,
            "title": title.strip()
        }

        # Sonuçları önbelleğe kaydet
        with open(cache_file_path, "w", encoding="utf-8") as f:
            json.dump(result_to_cache, f, ensure_ascii=False, indent=4)
        # Kullanıcının geçmişine ekle
        c.execute("INSERT INTO summaries (user_id, url, transcript, summary, sentiment_label, sentiment_score, video_type, tone, participants, title) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (user["id"], url, text, final_summary, sentiment_label, sentiment_score, video_type, tone, participants, title.strip()))
        conn.commit()
        print(f"Önbelleğe kaydedildi: {url}")

        await broadcast_progress(100, "İşlem tamamlandı!")
        
        return JSONResponse(content=result_to_cache, status_code=200)

    except Exception as e:
        import traceback
        print(f"HATA DETAYI:")
        traceback.print_exc()
        await broadcast_progress(0, f"Hata oluştu: {str(e)}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

# Kullanıcı kayıt endpointi
@app.post("/register/")
async def register(user: UserRegister):
    hashed_password = get_password_hash(user.password)
    try:
        c.execute("INSERT INTO users (email, hashed_password) VALUES (?, ?)", (user.email, hashed_password))
        conn.commit()
        return {"msg": "Kayıt başarılı"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Bu e-posta ile zaten bir kullanıcı var.")

# Kullanıcı giriş endpointi
@app.post("/login/")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    c.execute("SELECT id, email, hashed_password FROM users WHERE email = ?", (form_data.username,))
    user = c.fetchone()
    if not user or not verify_password(form_data.password, user[2]):
        raise HTTPException(status_code=400, detail="Geçersiz e-posta veya şifre.")
    access_token = create_access_token(data={"sub": user[1], "user_id": user[0]})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/history/")
async def get_history(request: Request):
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token eksik veya geçersiz.")
    token = auth_header.split(" ")[1]
    user = get_current_user(token)
    c.execute("SELECT url, transcript, summary, sentiment_label, sentiment_score, video_type, tone, participants, title, created_at FROM summaries WHERE user_id=? ORDER BY created_at DESC", (user["id"],))
    rows = c.fetchall()
    history = [
        {
            "url": row[0],
            "transcript": row[1],
            "summary": row[2],
            "sentiment_label": row[3],
            "sentiment_score": row[4],
            "video_type": row[5],
            "tone": row[6],
            "participants": row[7],
            "title": row[8],
            "created_at": row[9],
        }
        for row in rows
    ]
    return JSONResponse(content=history, status_code=200)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
