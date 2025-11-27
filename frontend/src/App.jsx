import { useState, useRef, useEffect } from "react";
import axios from "axios";
import "./App.css";
import AdminDashboard from "./AdminDashboard";
import Payment from "./Payment";
import VoiceMode from "./VoiceMode";
import { API_URL } from "./config";

export default function App() {
  const [view, setView] = useState("chat"); // "chat", "admin", "payment", or "voice"
  const [agent, setAgent] = useState("math");
  const [message, setMessage] = useState("");
  const [chat, setChat] = useState([]);
  const [isRecording, setIsRecording] = useState(false);
  const [ttsVoice, setTtsVoice] = useState("en-US-Standard-C");
  const [isPlaying, setIsPlaying] = useState(false);
  const [audioUrl, setAudioUrl] = useState(null);
  const [isLoadingAudio, setIsLoadingAudio] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  
  const recognitionRef = useRef(null);
  const chatEndRef = useRef(null);
  const audioRef = useRef(null);
  const waveformRef = useRef(null);
  const animationFrameRef = useRef(null);
  const fileInputRef = useRef(null);

  // Initialize Speech Recognition
  useEffect(() => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;
      recognitionRef.current.lang = 'en-US';

      recognitionRef.current.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setMessage(transcript);
        setIsRecording(false);
        stopWaveform();
      };

      recognitionRef.current.onerror = () => {
        setIsRecording(false);
        stopWaveform();
      };

      recognitionRef.current.onend = () => {
        setIsRecording(false);
        stopWaveform();
      };
    }
  }, []);

  // Load user's voice preference
  useEffect(() => {
    const loadVoicePreference = async () => {
      try {
        const res = await axios.get(`${API_URL}/api/user/123/voice-preference`);
        setTtsVoice(res.data.voice);
      } catch (error) {
        console.error("Error loading voice preference:", error);
      }
    };
    loadVoicePreference();
    
    // Track page view
    axios.post(`${API_URL}/api/analytics/page-view`).catch(err => {
      console.error("Error tracking page view:", err);
    });
  }, []);

  // Auto-scroll to bottom of chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chat]);

  // Waveform animation
  const startWaveform = () => {
    if (!waveformRef.current) return;
    
    const bars = waveformRef.current.querySelectorAll('.wave-bar');
    const animate = () => {
      bars.forEach((bar, index) => {
        const height = Math.random() * 60 + 20;
        bar.style.height = `${height}%`;
        bar.style.transition = 'height 0.1s ease';
      });
      animationFrameRef.current = requestAnimationFrame(animate);
    };
    animate();
  };

  const stopWaveform = () => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }
    if (waveformRef.current) {
      const bars = waveformRef.current.querySelectorAll('.wave-bar');
      bars.forEach(bar => {
        bar.style.height = '20%';
      });
    }
  };

  const startRecording = () => {
    if (recognitionRef.current) {
      setIsRecording(true);
      recognitionRef.current.start();
      startWaveform();
    }
  };

  const stopRecording = () => {
    if (recognitionRef.current && isRecording) {
      recognitionRef.current.stop();
      setIsRecording(false);
      stopWaveform();
    }
  };

  const sendMessage = async (customMessage = null) => {
    const messageToSend = customMessage || message;
    if (!messageToSend.trim() && !selectedFile) return;

    const userMessage = messageToSend;
    setMessage("");
    setIsProcessing(true);

    // Add user message to chat
    setChat(prev => [...prev, { from: "user", text: userMessage }]);

    try {
      let res;
      
      // Handle file upload
      if (selectedFile) {
        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('userId', '123');
        formData.append('agentId', agent);
        formData.append('message', userMessage);
        
        res = await axios.post(`${API_URL}/api/upload`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
        
        setSelectedFile(null);
        if (fileInputRef.current) fileInputRef.current.value = '';
      } else {
        res = await axios.post(`${API_URL}/api/chat`, {
          userId: "123",
          agentId: agent,
          message: userMessage
        });
      }

      // Add agent response to chat
      setChat(prev => [...prev, { from: "agent", text: res.data.reply }]);

      // Text-to-Speech using backend
      if (ttsVoice !== "none") {
        speakTextBackend(res.data.reply);
      }
    } catch (error) {
      console.error("Error sending message:", error);
      setChat(prev => [...prev, { from: "system", text: "Error: Could not get response from agent." }]);
    } finally {
      setIsProcessing(false);
    }
  };

  const speakTextBackend = async (text) => {
    try {
      setIsLoadingAudio(true);
      setIsSpeaking(true);
      const res = await axios.post(`${API_URL}/api/tts`, {
        text: text,
        voice: ttsVoice
      }, {
        responseType: 'blob'
      });
      
      const audioBlob = new Blob([res.data], { type: 'audio/mpeg' });
      const url = URL.createObjectURL(audioBlob);
      setAudioUrl(url);
      
      // Auto-play the audio
      if (audioRef.current) {
        audioRef.current.src = url;
        audioRef.current.play();
      }
    } catch (error) {
      console.error("Error generating speech:", error);
      setIsSpeaking(false);
    } finally {
      setIsLoadingAudio(false);
    }
  };

  const toggleAudioPlayback = () => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause();
      } else {
        audioRef.current.play();
      }
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  const handleVoiceChange = async (newVoice) => {
    setTtsVoice(newVoice);
    // Save to backend
    try {
      await axios.post(`${API_URL}/api/user/123/voice-preference`, {
        voice: newVoice
      });
    } catch (error) {
      console.error("Error saving voice preference:", error);
    }
  };

  // Get available TTS voices
  const getAvailableVoices = () => {
    if ('speechSynthesis' in window) {
      const voices = window.speechSynthesis.getVoices();
      return voices.filter(v => v.lang.startsWith('en'));
    }
    return [];
  };

  const [availableVoices, setAvailableVoices] = useState([]);

  useEffect(() => {
    const loadVoices = () => {
      setAvailableVoices(getAvailableVoices());
    };
    
    loadVoices();
    if ('speechSynthesis' in window) {
      window.speechSynthesis.onvoiceschanged = loadVoices;
    }
  }, []);

  // Audio event handlers
  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.onplay = () => {
        setIsPlaying(true);
        setIsSpeaking(true);
      };
      audioRef.current.onpause = () => {
        setIsPlaying(false);
        setIsSpeaking(false);
      };
      audioRef.current.onended = () => {
        setIsPlaying(false);
        setIsSpeaking(false);
      };
    }
  }, []);

  if (view === "admin") {
    return <AdminDashboard onBackToChat={() => setView("chat")} />;
  }

  if (view === "payment") {
    return <Payment onBackToChat={() => setView("chat")} />;
  }

  if (view === "voice") {
    return (
      <VoiceMode 
        onExit={() => setView("chat")}
        onSendMessage={sendMessage}
        agent={agent}
        ttsVoice={ttsVoice}
        isProcessing={isProcessing}
        isSpeaking={isSpeaking}
      />
    );
  }

  return (
    <div className="app-container">
      <div className="chat-header">
        <h1>Multi-Agent Chat</h1>
        <div className="header-controls">
          <button 
            className="admin-toggle-btn"
            onClick={() => setView("voice")}
            title="Voice Mode"
          >
            🎙️ Voice
          </button>
          <button 
            className="admin-toggle-btn"
            onClick={() => setView("payment")}
            title="Payment"
          >
            💳 Payment
          </button>
          <button 
            className="admin-toggle-btn"
            onClick={() => setView("admin")}
            title="Admin Dashboard"
          >
            📊 Admin
          </button>
          <select 
            className="agent-select" 
            onChange={e => setAgent(e.target.value)} 
            value={agent}
          >
            <option value="math">Math Agent</option>
            <option value="english">English Agent</option>
            <option value="coding">Coding Agent</option>
            <option value="sales">Sales Agent</option>
            <option value="science">Science Agent</option>
            <option value="urdu">Urdu Agent</option>
            <option value="history">History Agent</option>
          </select>
          
          <select 
            className="voice-select" 
            onChange={e => handleVoiceChange(e.target.value)} 
            value={ttsVoice}
          >
            <option value="none">No Voice</option>
            <option value="en-US-Standard-C">Female 1</option>
            <option value="en-US-Standard-D">Male 1</option>
            <option value="en-US-Wavenet-F">Female 2 (Wavenet)</option>
            <option value="en-US-Wavenet-J">Male 2 (Wavenet)</option>
          </select>
        </div>
      </div>

      <div className="chat-container">
        <div className="chat-messages">
          {chat.length === 0 && (
            <div className="welcome-message">
              <p>👋 Welcome! Select an agent and start chatting.</p>
              <p>You can type or use voice input.</p>
            </div>
          )}
          {chat.map((m, i) => (
            <div key={i} className={`message ${m.from}`}>
              <div className="message-content">
                <div className="message-header">
                  <span className="message-sender">
                    {m.from === "user" ? "You" : m.from === "agent" ? agent.charAt(0).toUpperCase() + agent.slice(1) + " Agent" : "System"}
                  </span>
                </div>
                <div className="message-text">{m.text}</div>
              </div>
            </div>
          ))}
          <div ref={chatEndRef} />
        </div>

        <div className="input-container">
          <div className="input-wrapper">
            <textarea
              className="message-input"
              value={message}
              onChange={e => setMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your message or use voice input..."
              rows="1"
            />
            
            <div className="input-actions">
              <input 
                type="file"
                ref={fileInputRef}
                onChange={handleFileSelect}
                accept="image/*"
                style={{ display: 'none' }}
              />
              <button
                className="file-button"
                onClick={() => fileInputRef.current?.click()}
                title="Upload image"
              >
                {selectedFile ? (
                  <span>📎 {selectedFile.name.substring(0, 10)}...</span>
                ) : (
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M21 19V5C21 3.9 20.1 3 19 3H5C3.9 3 3 3.9 3 5V19C3 20.1 3.9 21 5 21H19C20.1 21 21 20.1 21 19ZM8.5 13.5L11 16.51L14.5 12L19 18H5L8.5 13.5Z" fill="currentColor"/>
                  </svg>
                )}
              </button>
              <button
                className={`mic-button ${isRecording ? "recording" : ""}`}
                onMouseDown={startRecording}
                onMouseUp={stopRecording}
                onTouchStart={startRecording}
                onTouchEnd={stopRecording}
                title="Hold to record"
              >
                {isRecording ? (
                  <div className="waveform-container" ref={waveformRef}>
                    <div className="wave-bar"></div>
                    <div className="wave-bar"></div>
                    <div className="wave-bar"></div>
                    <div className="wave-bar"></div>
                    <div className="wave-bar"></div>
                  </div>
                ) : (
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 1C10.34 1 9 2.34 9 4V12C9 13.66 10.34 15 12 15C13.66 15 15 13.66 15 12V4C15 2.34 13.66 1 12 1Z" fill="currentColor"/>
                    <path d="M19 10V12C19 15.87 15.87 19 12 19C8.13 19 5 15.87 5 12V10H3V12C3 16.97 7.03 21 12 21C16.97 21 21 16.97 21 12V10H19Z" fill="currentColor"/>
                  </svg>
                )}
              </button>
              
              <button 
                className="send-button" 
                onClick={() => sendMessage()}
                disabled={!message.trim() && !selectedFile}
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M2.01 21L23 12L2.01 3L2 10L17 12L2 14L2.01 21Z" fill="currentColor"/>
                </svg>
              </button>
            </div>
          </div>
        </div>

        {/* Audio Player */}
        <audio ref={audioRef} style={{ display: 'none' }} />
        
        {/* Speaking Animation */}
        {isSpeaking && (
          <div className="speaking-indicator">
            <div className="speaking-animation">
              <div className="sound-wave">
                <div className="wave-bar"></div>
                <div className="wave-bar"></div>
                <div className="wave-bar"></div>
                <div className="wave-bar"></div>
                <div className="wave-bar"></div>
              </div>
              <p className="speaking-text">🔊 AI is speaking...</p>
            </div>
          </div>
        )}
        
        {audioUrl && !isSpeaking && (
          <div className="audio-controls">
            <button 
              className="audio-control-btn"
              onClick={toggleAudioPlayback}
              disabled={isLoadingAudio}
            >
              {isLoadingAudio ? (
                <span>⏳ Loading...</span>
              ) : isPlaying ? (
                <span>⏸️ Pause</span>
              ) : (
                <span>▶️ Replay</span>
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
