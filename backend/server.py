import os
import io
import json
import logging
import chromadb
import stripe
import redis
from datetime import datetime, timedelta
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Header, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import google.generativeai as genai
from google.cloud import texttospeech
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy.orm import Session
from sqlalchemy import func

import models, database

# ----------------------------
# Load environment variables
# ----------------------------
load_dotenv()
logging.basicConfig(level=logging.INFO)

# ----------------------------
# Configure Rate Limiting
# ----------------------------
limiter = Limiter(key_func=get_remote_address)

# ----------------------------
# FastAPI app
# ----------------------------
app = FastAPI(
    title="Gemini Multi-Agent API",
    description="Multi-agent chat system using Google Gemini and TTS",
    version="1.0.0"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Create tables
models.Base.metadata.create_all(bind=database.engine)

# ----------------------------
# Configure Redis (Optional)
# ----------------------------
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
try:
    redis_client = redis.from_url(redis_url, decode_responses=True)
    redis_client.ping()
    logging.info("Redis connected successfully.")
except Exception as e:
    logging.warning(f"Redis connection failed: {e}. Rate limiting will use in-memory storage.")
    redis_client = None

# ----------------------------
# Configure Stripe
# ----------------------------
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
stripe_webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")

if stripe.api_key:
    logging.info("Stripe API configured.")
else:
    logging.warning("STRIPE_SECRET_KEY not found. Payment features disabled.")

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
# Configure Vector DB (ChromaDB)
# ----------------------------
chroma_client = chromadb.Client()
memory_collection = chroma_client.create_collection(name="agent_memory", get_or_create=True)

# ----------------------------
# Agents & Prompts
# ----------------------------
AGENTS = {
    "math": {
        "name": "Math Agent",
        "system_prompt": "You are Math Agent. ONLY answer math questions clearly and correctly."
    },
    "english": {
        "name": "English Agent",
        "system_prompt": "You are English Agent. ONLY answer English questions (grammar, meaning, vocabulary)."
    },
    "coding": {
        "name": "Coding Agent",
        "system_prompt": "You are Coding Agent. ONLY answer programming questions."
    },
    "sales": {
        "name": "Sales Agent",
        "system_prompt": "You are Sales Agent. ONLY answer sales/lead generation questions."
    },
    "science": {
        "name": "Science Agent",
        "system_prompt": "You are Science Agent. ONLY answer science questions (physics, chemistry, biology, astronomy)."
    },
    "urdu": {
        "name": "Urdu Agent",
        "system_prompt": "You are Urdu Agent. ONLY answer questions about Urdu language, literature, and culture."
    },
    "history": {
        "name": "History Agent",
        "system_prompt": "You are History Agent. ONLY answer history questions about events, people, and civilizations."
    }
}
DEFAULT_AGENT_PROMPT = "You are a general assistant. Politely inform the user that you can only answer Math, English, Coding, Sales, Science, Urdu, or History questions."

AVAILABLE_VOICES = {
    "Female 1": "en-US-Standard-C",
    "Male 1": "en-US-Standard-D",
    "Female 2 (Wavenet)": "en-US-Wavenet-F",
    "Male 2 (Wavenet)": "en-US-Wavenet-J",
}

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

class VoicePreference(BaseModel):
    voice: str

class PaymentRequest(BaseModel):
    amount: int  # in cents
    currency: str = "usd"
    userId: str

# ----------------------------
# Helper functions
# ----------------------------
async def classify_agent_llm(message: str, agent_id: Optional[str]):
    if agent_id and agent_id in AGENTS:
        return AGENTS[agent_id]["system_prompt"], agent_id

    if not genai_client:
        return DEFAULT_AGENT_PROMPT, "default"

    classification_prompt = f"""
    You are a smart router. Classify the following user message into one of these categories:
    - math
    - english
    - coding
    - sales
    - science
    - urdu
    - history
    - other

    User Message: "{message}"

    Respond ONLY with the category name.
    """
    
    try:
        model = genai_client.GenerativeModel("gemini-2.0-flash")
        response = await model.generate_content_async(classification_prompt)
        category = response.text.strip().lower()
        
        if category in AGENTS:
            return AGENTS[category]["system_prompt"], category
        else:
            return DEFAULT_AGENT_PROMPT, "default"
    except Exception as e:
        logging.error(f"Router error: {e}")
        return DEFAULT_AGENT_PROMPT, "default"

async def generate_gemini_response(system_prompt: str, user_message: str, context: str = "") -> str:
    if not genai_client:
        logging.info(f"[MOCK] {user_message}")
        return f"Mock reply for category: {system_prompt.split('.')[0]}"
    try:
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        model = genai_client.GenerativeModel(model_name)
        
        full_prompt = f"{system_prompt}\n\nContext from previous conversations:\n{context}\n\nUser Question: {user_message}"
        
        response = await model.generate_content_async(full_prompt)
        return response.text
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
@limiter.limit("20/minute")
async def chat_handler(request: Request, chat_request: ChatRequest, db: Session = Depends(database.get_db)):
    user_id = chat_request.userId or "guest"
    
    # 1. Retrieve Context from Memory
    results = memory_collection.query(
        query_texts=[chat_request.message],
        n_results=2,
        where={"user_id": user_id}
    )
    context = ""
    if results['documents']:
        context = "\n".join(results['documents'][0])

    # 2. Classify Intent
    system_prompt, agent_name = await classify_agent_llm(chat_request.message, chat_request.agentId)
    
    # 3. Generate Response
    reply = await generate_gemini_response(system_prompt, chat_request.message, context)
    
    # 4. Save to Memory (Vector DB)
    memory_collection.add(
        documents=[f"User: {chat_request.message}\nAgent: {reply}"],
        metadatas=[{"user_id": user_id, "agent": agent_name}],
        ids=[f"{user_id}_{os.urandom(4).hex()}"]
    )

    # 5. Save to DB (Persistence)
    # Ensure user exists
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        user = models.User(id=user_id, message_count=0)
        db.add(user)
        db.flush()  # Ensure user is created before updating
    
    user.last_seen = datetime.utcnow()
    if user.message_count is None:
        user.message_count = 0
    user.message_count += 1
    
    # Save message
    db_message = models.Message(
        user_id=user_id,
        agent_id=agent_name,
        user_message=chat_request.message,
        agent_reply=reply
    )
    db.add(db_message)
    db.commit()
    
    return ChatResponse(reply=reply, agentName=agent_name)

@app.post("/api/tts")
async def tts_handler(request: TTSRequest):
    audio_bytes = await synthesize_speech(request.text, request.voice or "en-US-Standard-C")
    return StreamingResponse(io.BytesIO(audio_bytes), media_type="audio/mpeg")

@app.get("/api/voices")
async def get_voices():
    return AVAILABLE_VOICES

@app.get("/api/user/{user_id}/voice-preference")
async def get_voice_preference(user_id: str, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user:
        return {"voice": user.voice_preference}
    return {"voice": "en-US-Standard-C"}

@app.post("/api/user/{user_id}/voice-preference")
async def save_voice_preference(user_id: str, preference: VoicePreference, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        user = models.User(id=user_id)
        db.add(user)
    
    user.voice_preference = preference.voice
    db.commit()
    return {"status": "success", "voice": preference.voice}

# ----------------------------
# Analytics Endpoints
# ----------------------------
@app.post("/api/analytics/page-view")
async def track_page_view_endpoint(db: Session = Depends(database.get_db)):
    # Assuming a singleton row for analytics for simplicity, or we could track individual events
    analytics = db.query(models.Analytics).first()
    if not analytics:
        analytics = models.Analytics(page_views=0)
        db.add(analytics)
    
    analytics.page_views += 1
    db.commit()
    return {"status": "success"}

# ----------------------------
# Admin Dashboard Endpoints
# ----------------------------
@app.get("/api/admin/analytics")
async def get_admin_analytics(db: Session = Depends(database.get_db)):
    analytics = db.query(models.Analytics).first()
    page_views = analytics.page_views if analytics else 0
    
    total_messages = db.query(models.Message).count()
    unique_users = db.query(models.User).count()
    
    # Top agents
    agent_counts = db.query(models.Message.agent_id, func.count(models.Message.id)).group_by(models.Message.agent_id).all()
    top_agents = [{"agentId": agent, "count": count} for agent, count in sorted(agent_counts, key=lambda x: x[1], reverse=True)]
    
    return {
        "summary": {
            "totalPageViews": page_views,
            "totalMessages": total_messages,
            "uniqueUsers": unique_users,
            "averageMessagesPerUser": total_messages / unique_users if unique_users > 0 else 0,
            "topAgents": top_agents
        }
    }

@app.get("/api/admin/stats")
async def get_admin_stats(db: Session = Depends(database.get_db)):
    analytics = db.query(models.Analytics).first()
    page_views = analytics.page_views if analytics else 0
    
    total_messages = db.query(models.Message).count()
    unique_users = db.query(models.User).count()
    
    # Top agents
    agent_counts = db.query(models.Message.agent_id, func.count(models.Message.id)).group_by(models.Message.agent_id).all()
    top_agents = [{"agentId": agent, "count": count} for agent, count in sorted(agent_counts, key=lambda x: x[1], reverse=True)]
    
    # Recent activity
    recent_messages = db.query(models.Message).order_by(models.Message.timestamp.desc()).limit(10).all()
    recent_activity = [{
        "userId": msg.user_id,
        "agentId": msg.agent_id,
        "timestamp": msg.timestamp.isoformat()
    } for msg in recent_messages]
    
    return {
        "totalPageViews": page_views,
        "totalMessages": total_messages,
        "uniqueUsers": unique_users,
        "topAgents": top_agents,
        "recentActivity": {
            "messages": recent_activity
        }
    }

@app.get("/api/admin/users")
async def get_admin_users(db: Session = Depends(database.get_db)):
    users = db.query(models.User).all()
    
    users_data = []
    for user in users:
        # Get agents used by this user
        agents_used = db.query(models.Message.agent_id).filter(models.Message.user_id == user.id).distinct().all()
        agents_used = [a[0] for a in agents_used]
        
        users_data.append({
            "userId": user.id,
            "messageCount": user.message_count,
            "agentsUsed": agents_used,
            "firstSeen": user.first_seen.isoformat() if user.first_seen else None,
            "lastSeen": user.last_seen.isoformat() if user.last_seen else None
        })
    
    return {
        "total": len(users_data),
        "users": users_data
    }

@app.get("/api/admin/revenue")
async def get_admin_revenue(db: Session = Depends(database.get_db)):
    transactions = db.query(models.Transaction).all()
    total_revenue = sum([t.amount for t in transactions])
    
    return {
        "totalRevenue": total_revenue,
        "transactions": len(transactions),
        "revenue": [{
            "sessionId": t.session_id,
            "amount": t.amount,
            "currency": t.currency,
            "userId": t.user_id,
            "timestamp": t.timestamp.isoformat(),
            "status": t.status
        } for t in transactions]
    }

# ----------------------------
# Stripe Payment Endpoints
# ----------------------------
@app.post("/api/payment/create-checkout-session")
async def create_checkout_session(payment_request: PaymentRequest):
    if not stripe.api_key:
        raise HTTPException(status_code=501, detail="Stripe not configured")
    
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': payment_request.currency,
                    'product_data': {
                        'name': 'AI Agent Subscription',
                    },
                    'unit_amount': payment_request.amount,
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=f'http://localhost:5173/?payment=success&session_id={{CHECKOUT_SESSION_ID}}',
            cancel_url='http://localhost:5173/?payment=cancel',
            metadata={'userId': payment_request.userId}
        )
        
        return {"sessionId": checkout_session.id, "url": checkout_session.url}
    except Exception as e:
        logging.error(f"Stripe error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/payment/confirm")
async def confirm_payment(request: Request, db: Session = Depends(database.get_db)):
    """Confirm payment and record transaction after successful Stripe checkout"""
    if not stripe.api_key:
        raise HTTPException(status_code=501, detail="Stripe not configured")
    
    data = await request.json()
    session_id = data.get('sessionId')
    
    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID required")
    
    try:
        # Retrieve the session from Stripe
        session = stripe.checkout.Session.retrieve(session_id)
        
        # Check if payment was successful
        if session.payment_status == 'paid':
            # Check if already recorded
            existing = db.query(models.Transaction).filter(models.Transaction.session_id == session_id).first()
            
            if not existing:
                user_id = session.metadata.get('userId')
                
                # Ensure user exists
                user = db.query(models.User).filter(models.User.id == user_id).first()
                if not user:
                    user = models.User(id=user_id)
                    db.add(user)
                    db.commit() # Commit to get user ID if it was auto-generated (though here it's string)
                
                transaction = models.Transaction(
                    session_id=session_id,
                    amount=session.amount_total / 100,
                    currency=session.currency,
                    user_id=user_id,
                    status="completed"
                )
                db.add(transaction)
                db.commit()
                
                logging.info(f"Payment confirmed for user {user_id}: ${session.amount_total / 100}")
            
            return {
                "status": "success",
                "amount": session.amount_total / 100,
                "currency": session.currency
            }
        else:
            return {
                "status": "pending",
                "paymentStatus": session.payment_status
            }
    except Exception as e:
        logging.error(f"Error confirming payment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ----------------------------
# File Upload Endpoint
# ----------------------------
@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    userId: str = "guest",
    agentId: str = "default",
    message: str = "",
    db: Session = Depends(database.get_db)
):
    """Handle file uploads and analyze with Gemini Vision"""
    if not genai_client:
        raise HTTPException(status_code=501, detail="Gemini API not configured")
    
    try:
        # Read file content
        file_content = await file.read()
        
        # Determine file type
        content_type = file.content_type or ""
        
        # Prepare the file for Gemini
        if content_type.startswith("image/"):
            # Use Gemini Pro Vision for images
            model = genai_client.GenerativeModel("gemini-2.0-flash-exp")
            
            # Create image part
            image_part = {
                "mime_type": content_type,
                "data": file_content
            }
            
            # Create prompt
            prompt = message or "Describe this image in detail."
            
            # Generate response
            response = await model.generate_content_async([prompt, image_part])
            reply = response.text
            
        else:
            raise HTTPException(status_code=400, detail="Only image files are supported currently")
        
        # Save to database
        user = db.query(models.User).filter(models.User.id == userId).first()
        if not user:
            user = models.User(id=userId)
            db.add(user)
        
        user.last_seen = datetime.utcnow()
        user.message_count += 1
        
        db_message = models.Message(
            user_id=userId,
            agent_id=agentId,
            user_message=f"[Uploaded: {file.filename}] {message}",
            agent_reply=reply
        )
        db.add(db_message)
        db.commit()
        
        return {
            "reply": reply,
            "agentName": agentId,
            "filename": file.filename
        }
        
    except Exception as e:
        logging.error(f"Error processing file upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))
