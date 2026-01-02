import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import './App.css';
import ChatMessage from './components/ChatMessage';
import MovieCard from './components/MovieCard';
import LoadingSpinner from './components/LoadingSpinner';

const API_URL = 'http://localhost:8000/chat';

function App() {
  const [messages, setMessages] = useState([
    {
      type: 'bot',
      text: "Hi! I'm your emotion-aware movie recommender. Tell me how you're feeling or what kind of movie you want, and I'll suggest some great films! 🎬",
      timestamp: new Date()
    }
  ]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const [sessionId] = useState(() => 'session_' + Math.random().toString(36).slice(2));

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async (e) => {
    e.preventDefault();
    
    if (!inputText.trim() || isLoading) {
      return;
    }

    const userMessage = inputText.trim();
    setInputText('');
    setError(null);

    // Add user message
    const newUserMessage = {
      type: 'user',
      text: userMessage,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, newUserMessage]);
    setIsLoading(true);

    try {
      const response = await axios.post(API_URL, {
        text: userMessage,
        session_id: sessionId,
        threshold: 0.2,
        top_k: 5
      }, {
        timeout: 30000, // 30 second timeout
        headers: {
          'Content-Type': 'application/json'
        }
      });

      const data = response.data;

      // Add bot reply
      const botMessage = {
        type: 'bot',
        text: data.reply || "I couldn't process that request. Please try again.",
        timestamp: new Date(),
        movies: data.movies || [],
        genreScores: data.genre_scores || [],
        mlScores: data.ml_scores || {}
      };
      
      setMessages(prev => [...prev, botMessage]);

    } catch (err) {
      console.error('API Error:', err);
      
      let errorMessage = "I'm having trouble connecting to the recommendation service. ";
      
      if (err.response) {
        // Server responded with error
        const status = err.response.status;
        if (status === 400) {
          errorMessage = "Please provide a valid message. Try describing how you're feeling or what kind of movie you want.";
        } else if (status === 500) {
          errorMessage = "The recommendation service encountered an error. Please try again in a moment.";
        } else {
          errorMessage = `Server error (${status}). Please try again.`;
        }
      } else if (err.request) {
        // Request made but no response
        errorMessage = "I can't reach the recommendation service right now. Please check if the API server is running on http://localhost:8000";
      } else if (err.code === 'ECONNABORTED') {
        errorMessage = "The request took too long. Please try again with a shorter message.";
      } else {
        errorMessage = "An unexpected error occurred. Please try again.";
      }

      const errorBotMessage = {
        type: 'bot',
        text: errorMessage,
        timestamp: new Date(),
        isError: true
      };
      
      setMessages(prev => [...prev, errorBotMessage]);
      setError(errorMessage);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend(e);
    }
  };

  const clearChat = () => {
    setMessages([
      {
        type: 'bot',
        text: "Chat cleared! How can I help you find a movie today? 🎬",
        timestamp: new Date()
      }
    ]);
    setError(null);
  };

  return (
    <div className="app">
      <div className="chat-container">
        <div className="chat-header">
          <h1>🎬 Emotion Movie Recommender</h1>
          <button className="clear-button" onClick={clearChat} title="Clear chat">
            Clear
          </button>
        </div>

        <div className="messages-container">
          {messages.map((message, index) => (
            <ChatMessage key={index} message={message} />
          ))}
          
          {isLoading && (
            <div className="message bot-message">
              <div className="message-content">
                <LoadingSpinner />
                <span className="loading-text">Analyzing your emotions and finding movies...</span>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        <form className="input-form" onSubmit={handleSend}>
          <input
            ref={inputRef}
            type="text"
            className="chat-input"
            placeholder="Tell me how you're feeling or what movie you want..."
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={isLoading}
            autoFocus
          />
          <button
            type="submit"
            className="send-button"
            disabled={!inputText.trim() || isLoading}
            title="Send message"
          >
            {isLoading ? '⏳' : '📤'}
          </button>
        </form>

        {error && (
          <div className="error-banner">
            ⚠️ {error}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;

