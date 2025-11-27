import { useState, useEffect, useRef } from "react";
import "./VoiceMode.css";

export default function VoiceMode({ 
  onExit, 
  onSendMessage, 
  agent, 
  ttsVoice,
  isProcessing,
  isSpeaking 
}) {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [lastResponse, setLastResponse] = useState("");
  const recognitionRef = useRef(null);
  const animationFrameRef = useRef(null);

  // Initialize Speech Recognition
  useEffect(() => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = true;
      recognitionRef.current.lang = 'en-US';

      recognitionRef.current.onresult = (event) => {
        const current = event.resultIndex;
        const transcriptText = event.results[current][0].transcript;
        setTranscript(transcriptText);
        
        // If final result, send message
        if (event.results[current].isFinal) {
          setIsListening(false);
          onSendMessage(transcriptText);
          setTranscript("");
        }
      };

      recognitionRef.current.onerror = (event) => {
        console.error("Speech recognition error:", event.error);
        setIsListening(false);
      };

      recognitionRef.current.onend = () => {
        setIsListening(false);
      };
    }

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, [onSendMessage]);

  const startListening = () => {
    if (recognitionRef.current && !isListening) {
      setIsListening(true);
      recognitionRef.current.start();
    }
  };

  const stopListening = () => {
    if (recognitionRef.current && isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    }
  };

  const getStatus = () => {
    if (isSpeaking) return "Speaking";
    if (isProcessing) return "Thinking";
    if (isListening) return "Listening";
    return "Tap to speak";
  };

  const getStatusClass = () => {
    if (isSpeaking) return "speaking";
    if (isProcessing) return "processing";
    if (isListening) return "listening";
    return "idle";
  };

  return (
    <div className="voice-mode-container">
      <div className="voice-mode-header">
        <h2>{agent.charAt(0).toUpperCase() + agent.slice(1)} Agent</h2>
        <button className="exit-voice-mode" onClick={onExit}>
          ✕ Exit Voice Mode
        </button>
      </div>

      <div className="voice-mode-content">
        <div className={`voice-visualizer ${getStatusClass()}`}>
          <div className="pulse-ring pulse-ring-1"></div>
          <div className="pulse-ring pulse-ring-2"></div>
          <div className="pulse-ring pulse-ring-3"></div>
          <div className="center-circle" onClick={isListening ? stopListening : startListening}>
            <div className="inner-circle">
              {isListening && "🎤"}
              {isSpeaking && "🔊"}
              {isProcessing && "⚡"}
              {!isListening && !isSpeaking && !isProcessing && "🎙️"}
            </div>
          </div>
        </div>

        <div className="voice-status">
          <h3>{getStatus()}</h3>
          {transcript && (
            <p className="transcript-preview">{transcript}</p>
          )}
        </div>

        <div className="voice-controls">
          <button 
            className={`voice-control-btn ${isListening ? 'active' : ''}`}
            onClick={isListening ? stopListening : startListening}
          >
            {isListening ? "⏹️ Stop" : "🎤 Start"}
          </button>
        </div>
      </div>
    </div>
  );
}
