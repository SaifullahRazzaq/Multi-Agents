import os
import io
import json
import asyncio
import logging
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import google.generativeai as genai
from google.cloud import texttospeech

# ----------------------------
# Load environment variables
# ----------------------------
load_dotenv()
logging.basicConfig(level=logging.INFO)

# ----------------------------
# FastAPI app
# ----------------------------
app = FastAPI(
    title="Gemini Multi-Agent API",
    description="Multi-agent chat system using Google Gemini and TTS",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# ----------------------------
# Configure Gemini API
# ----------------------------
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    logging.warning("GEMINI_API_KEY not found. Using mock responses.")
    genai_client = None
else:
    genai.configure(api_key=api_key)
    genai_client = genai
    logging.info("Gemini API configured.")

# ----------------------------
# Configure TTS
# ----------------------------
try:
    tts_client = texttospeech.TextToSpeechAsyncClient()
    logging.info("Google Cloud TTS client configured.")
except Exception as e:
    logging.error(f"TTS client config error: {e}")
    tts_client = None

# ----------------------------
# Agents & Prompts
# ----------------------------
AGENTS = {
    "math": {
        "name": "Math Agent",
        "keywords": ['math', 'calculate', 'add', 'subtract', 'multiply', 'divide', 'equation', 'number'],
        "system_prompt": "You are Math Agent. ONLY answer math questions clearly and correctly."
    },
    "english": {
        "name": "English Agent",
        "keywords": ['english', 'grammar', 'sentence', 'meaning', 'translate', 'word'],
        "system_prompt": "You are English Agent. ONLY answer English questions (grammar, meaning, vocabulary)."
    },
    "coding": {
        "name": "Coding Agent",
        "keywords": ['code', 'python', 'javascript', 'react', 'fastapi', 'error', 'debug', 'program'],
        "system_prompt": "You are Coding Agent. ONLY answer programming questions."
    },
    "sales": {
        "name": "Sales Agent",
        "keywords": ['buy', 'sell', 'product', 'price', 'sales', 'cost'],
        "system_prompt": "You are Sales Agent. ONLY answer sales/lead generation questions."
    }
}
DEFAULT_AGENT_PROMPT = "You are a general assistant. Politely inform the user that you can only answer Math, English, Coding, or Sales questions."

AVAILABLE_VOICES = {
    "Female 1": "en-US-Standard-C",
    "Male 1": "en-US-Standard-D",
    "Female 2 (Wavenet)": "en-US-Wavenet-F",
    "Male 2 (Wavenet)": "en-US-Wavenet-J",
}

DB_FILE = "conversations.json"

# ----------------------------
# Pydantic Models
# ----------------------------
class ChatRequest(BaseModel):
    message: str
    userId: Optional[str] = None
    agentId: Optional[str] = None

class ChatResponse(BaseModel):
    reply: str
    agentName: str

class TTSRequest(BaseModel):
    text: str
    voice: Optional[str] = "en-US-Standard-C"

# ----------------------------
# Helper functions
# ----------------------------
async def read_db():
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, 'r') as f:
        return json.load(f)

async def write_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=2)

async def classify_agent(message: str, agent_id: Optional[str]):
    if agent_id and agent_id in AGENTS:
        return AGENTS[agent_id]["system_prompt"], agent_id
    lower_msg = message.lower()
    for name, data in AGENTS.items():
        if any(kw in lower_msg for kw in data["keywords"]):
            return data["system_prompt"], name
    return DEFAULT_AGENT_PROMPT, "default"

async def generate_gemini_response(system_prompt: str, user_message: str) -> str:
    if not genai_client:
        logging.info(f"[MOCK] {user_message}")
        return f"Mock reply for category: {system_prompt.split('.')[0]}"
    try:
        response = await genai.chat(
            model=os.getenv("GEMINI_MODEL", "gemini-1"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.2
        )
        return response.last
    except Exception as e:
        logging.error(f"Gemini API call failed: {e}")
        raise HTTPException(status_code=500, detail=f"Gemini API error: {str(e)}")

async def synthesize_speech(text: str, voice_name: str):
    if not tts_client:
        raise HTTPException(status_code=501, detail="TTS not configured")
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        name=voice_name
    )
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
    response = await tts_client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )
    return response.audio_content

# ----------------------------
# API Endpoints
# ----------------------------
@app.get("/")
async def root():
    return {"message": "Gemini Multi-Agent Backend is running."}

@app.post("/api/chat", response_model=ChatResponse)
async def chat_handler(request: ChatRequest):
    system_prompt, agent_name = await classify_agent(request.message, request.agentId)
    reply = await generate_gemini_response(system_prompt, request.message)
    # Save conversation
    db = await read_db()
    db.setdefault(request.userId or "guest", []).append({"agent": agent_name, "user": request.message, "reply": reply})
    await write_db(db)
    return ChatResponse(reply=reply, agentName=agent_name)

@app.post("/api/tts")
async def tts_handler(request: TTSRequest):
    audio_bytes = await synthesize_speech(request.text, request.voice or "en-US-Standard-C")
    return StreamingResponse(io.BytesIO(audio_bytes), media_type="audio/mpeg")

@app.get("/api/voices")
async def get_voices():
    return AVAILABLE_VOICES
