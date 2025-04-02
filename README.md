# Video Summary Tool

An intelligent tool for generating concise text summaries from video content (YouTube links or local MP4 files). This project uses AI-based transcription and summarization models to provide quick, high-level overviews of long videos.

## 🚀 Features

- 🎥 Upload or link YouTube / MP4 videos
- 🧠 AI-powered transcription using Whisper
- 📝 Automatic summarization using LLMs (e.g., T5 / BART / GPT)
- 💡 Simple and intuitive web interface (React)
- 📄 Output: clean and readable text summaries

## 🧰 Tech Stack

- **Frontend**: React.js, Tailwind CSS
- **Backend**: Python (Flask / FastAPI)
- **Transcription**: OpenAI Whisper
- **Summarization**: HuggingFace Transformers (T5, BART, etc.)
- **Others**: ffmpeg, pytube, moviepy

## 📦 Installation

```bash
git clone https://github.com/kullanici-adin/video-summary-tool.git
cd video-summary-tool

## 🛠️ How It Works

1. User uploads a video or provides a YouTube link.
2. The backend extracts audio and transcribes it into text using Whisper.
3. The transcribed text is summarized using a transformer-based language model.
4. The summary is returned and displayed on the interface.

## 📌 TODO

- [ ] Drag & drop video upload
- [ ] Summarization model fine-tuning
- [ ] Multiple language support
- [ ] PDF / TXT export of summaries

## 🤝 Contributing

Contributions, issues and feature requests are welcome!  
Feel free to open a pull request or fork the repo.

## 📄 License

MIT License

---

Feel free to contribute or suggest improvements!
