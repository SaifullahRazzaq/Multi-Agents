# Gemini Project Task List

## 1. Project Setup
- Create GitHub repo
- Make frontend + backend folders
- Initialize package.json in both
- Add README describing project

## 2. Core Features
- Create multi-agent system (Math, English, Coding, Sales)
- Each agent must answer ONLY its subject
- Out-of-scope → redirect message
- All answers come from Gemini API
- Add conversation history
- Add user authentication

## 3. UI Features
- Text chat
- Voice input option
- Voice output (AI speaking answer)
- Add option to choose TTS voice
- Add mic button + waveform

## 4. Backend Tasks
- Build /chat endpoint
- Build agent router
- Add topic classifier (keyword-based)
- Add Gemini API client
- Add vector DB for memory (optional)
- Add conversation save in database

## 5. Voice Features
- Use Gemini Text-to-Speech
- Store user's selected voice in DB
- Add audio streaming support
- Add play/pause audio buttons

## 6. Advanced Integrations
- Add Stripe payments
- Add Admin dashboard
- Add rate limiting (Redis)
- Add analytics (page views, messages count)

## 7. Deployment
- Deploy frontend → Vercel
- Deploy backend → Render/AWS
- Deploy DB → Supabase
- Environment variables setup

## 8. Testing & QA
- Unit tests for agent router
- Integration tests for /chat
- UI tests for chat interface
- Voice recognition tests

## 9. Future Enhancements
- Add more agents (science, Urdu, history)
- Add agent-to-agent communication
- Add file uploader for worksheets
- Add dynamic voice cloning



