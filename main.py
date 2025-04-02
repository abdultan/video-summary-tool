from fastapi import FastAPI, File, UploadFile
import uvicorn
import subprocess
from pathlib import Path
import os
import whisper
import asyncio

app = FastAPI()

UPLOAD_DIR = "uploads"
AUDIO_DIR = "audio"
FFMPEG_PATH = r"C:\ffmpeg-7.1.1-essentials_build\ffmpeg-7.1.1-essentials_build\bin\ffmpeg.exe"  # FFmpeg'in tam yolu

# Klasörleri oluştur
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)

model = whisper.load_model("medium")

@app.post("/upload/")
async def upload_video(file: UploadFile = File(...)):
    """Video dosyasını yükler ve kaydeder."""
    file_path = Path(UPLOAD_DIR) / file.filename
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    return {"message": "Video yüklendi", "filename": file.filename}


@app.post("/extract-audio/")
async def extract_audio(filename: str):
    """Yüklenen videodan sesi çıkarır."""
    try:
        video_path = Path(UPLOAD_DIR) / filename
        audio_path = Path(AUDIO_DIR) / f"{Path(filename).stem}.wav"

        if not video_path.exists():
            return {"error": "Video dosyası bulunamadı.", "filename": filename}

        # Eğer ses dosyası zaten varsa, işlem yapmadan döndür
        if audio_path.exists():
            print(f"✅ Ses dosyası zaten mevcut: {audio_path}")
            return {"message": "Ses dosyası zaten mevcut.", "audio_file": str(audio_path)}

        command = [FFMPEG_PATH, "-i", str(video_path), "-q:a", "0", "-map", "a", str(audio_path)]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode != 0:
            return {"error": "FFmpeg çalıştırılırken hata oluştu.", "details": result.stderr}

        # 🛠 FFmpeg çıktıktan sonra, gerçekten dosyanın var olup olmadığını kontrol edelim
        if not audio_path.exists():
            return {"error": "FFmpeg çıktı ama ses dosyası oluşturulmadı!", "filename": filename}

        print(f"✅ Ses dosyası başarıyla oluşturuldu: {audio_path}")

        return {"message": "Ses çıkarıldı", "audio_file": str(audio_path)}

    except Exception as e:
        return {"error": "Bilinmeyen bir hata oluştu.", "details": str(e)}



TRANSCRIPTION_DIR = "transcriptions"
os.makedirs(TRANSCRIPTION_DIR, exist_ok=True)

@app.post("/transcribe-audio/")
async def transcribe_audio(filename: str):
    """Çıkarılan sesi metne çevirir."""
    try:
        audio_path = Path(AUDIO_DIR) / f"{Path(filename).stem}.wav"
        absolute_audio_path = audio_path.resolve(strict=False)  # Mutlak yolu al

        print(f"✅ API'nin kontrol ettiği dosya yolu: {absolute_audio_path}")

        # Dosyanın okunup okunamadığını kontrol edelim
        try:
            with open(absolute_audio_path, "rb") as f:
                print("✅ Dosya başarıyla açıldı ve okunabilir!")
        except FileNotFoundError:
            return {"error": "Ses dosyası bulunamadı (FileNotFoundError).", "filename": filename, "path_checked": str(absolute_audio_path)}
        except PermissionError:
            return {"error": "Dosya erişim izni hatası! (PermissionError)", "filename": filename, "path_checked": str(absolute_audio_path)}

        # Whisper çalıştır
        result = model.transcribe(str(absolute_audio_path), language="tr")

        return {"message": "Transkripsiyon tamamlandı", "text": result["text"]}

    except Exception as e:
        return {"error": "Bilinmeyen bir hata oluştu.", "details": str(e)}


import os

print(f"✅ API Çalışma Dizini: {os.getcwd()}")
print(f"📂 'audio' Klasör Durumu: {os.path.exists('audio')}")
print(f"📂 'audio' İçeriği: {os.listdir('audio') if os.path.exists('audio') else 'Klasör Yok'}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)


