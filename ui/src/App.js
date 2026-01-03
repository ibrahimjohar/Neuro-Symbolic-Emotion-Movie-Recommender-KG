import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import './App.css';
import ChatMessage from './components/ChatMessage';
import LoadingSpinner from './components/LoadingSpinner';
import Header from './components/Header';
import About from './pages/About';
import { Routes, Route } from 'react-router-dom';
import HighlightPanel from './components/HighlightPanel';
import InfoPanel from './components/InfoPanel';
import Footer from './components/Footer';

const API_URL = 'http://localhost:8000/chat';
const DETAILS_API_URL = 'http://localhost:8000/movie/details';

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
  const [sessionId, setSessionId] = useState(() => {
    const saved = localStorage.getItem('sessionId');
    if (saved) return saved;
    const id = 'session_' + Math.random().toString(36).slice(2);
    localStorage.setItem('sessionId', id);
    return id;
  });
  // highlight panel state
  const [showHighlight, setShowHighlight] = useState(true);
  const [highlightMovies, setHighlightMovies] = useState([]);
  const [highlightIndex, setHighlightIndex] = useState(0);
  const [highlightDetails, setHighlightDetails] = useState(null);
  const [highlightLoading, setHighlightLoading] = useState(false);
  const detailsCacheRef = useRef(new Map());
  const [posterReady, setPosterReady] = useState(false);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const fetchHighlightDetails = async (title, year) => {
    if (!title) return;
    const key = `${title}|${year || ''}`;
    if (detailsCacheRef.current.has(key)) {
      setHighlightDetails(detailsCacheRef.current.get(key));
      return;
    }
    setHighlightLoading(true);
    try {
      const res = await axios.post(DETAILS_API_URL, { title, year }, { timeout: 15000 });
      const details = res?.data?.details || null;
      if (details) {
        detailsCacheRef.current.set(key, details);
        setHighlightDetails(details);
      } else {
        setHighlightDetails(null);
      }
    } catch (e) {
      console.error('Details fetch failed', e);
      setHighlightDetails(null);
    } finally {
      setHighlightLoading(false);
    }
  };

  const prefetchDetailsForMovies = async (movies) => {
    try {
      const tasks = (movies || []).slice(0, 5).map(m => {
        const key = `${m?.title}|${m?.year || ''}`;
        if (detailsCacheRef.current.has(key)) return Promise.resolve(detailsCacheRef.current.get(key));
        return axios.post(DETAILS_API_URL, { title: m?.title, year: m?.year }, { timeout: 12000 })
          .then(res => {
            const det = res?.data?.details || null;
            if (det) {
              detailsCacheRef.current.set(key, det);
              if (det.poster_url) {
                const img = new Image();
                img.src = det.poster_url;
              }
            }
            return det;
          })
          .catch(() => null);
      });
      await Promise.all(tasks);
    } catch (e) {
      // ignore prefetch errors
    }
  };
  const handleNextHighlight = () => {
    if (!highlightMovies.length) return;
    const next = (highlightIndex + 1) % highlightMovies.length;
    setHighlightIndex(next);
    const m = highlightMovies[next];
    fetchHighlightDetails(m?.title, m?.year);
  };
  const handlePrevHighlight = () => {
    if (!highlightMovies.length) return;
    const prev = (highlightIndex - 1 + highlightMovies.length) % highlightMovies.length;
    setHighlightIndex(prev);
    const m = highlightMovies[prev];
    fetchHighlightDetails(m?.title, m?.year);
  };
  const toggleHighlight = () => setShowHighlight(s => !s);

  const handleMovieSelect = (movie, index, list) => {
    if (Array.isArray(list) && list.length) {
      setHighlightMovies(list);
    }
    if (typeof index === 'number') {
      setHighlightIndex(index);
    }
    setPosterReady(false);
    fetchHighlightDetails(movie?.title, movie?.year);
    setShowHighlight(true);
  };

  const handleSend = async (e) => {
    e.preventDefault();
    
    if (!inputText.trim() || isLoading) {
      return;
    }

    const userMessage = inputText.trim();
    setInputText('');
    setError(null);

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
        rating_threshold: 7.0,
        top_k: 5
      }, {
        timeout: 30000,
        headers: {
          'Content-Type': 'application/json'
        }
      });

      const data = response.data;

      const botMessage = {
        type: 'bot',
        text: data.reply || "I couldn't process that request. Please try again.",
        timestamp: new Date(),
        movies: data.movies || [],
        genreScores: data.genre_scores || [],
        mlScores: data.ml_scores || {}
      };
      setMessages(prev => [...prev, botMessage]);

      // update highlight movies and fetch first details
      if (Array.isArray(botMessage.movies) && botMessage.movies.length) {
        setHighlightMovies(botMessage.movies);
        setHighlightIndex(0);
        const first = botMessage.movies[0];
        setPosterReady(false);
        fetchHighlightDetails(first?.title, first?.year);
        prefetchDetailsForMovies(botMessage.movies);
      }

    } catch (err) {
      console.error('API Error:', err);
      
      let errorMessage = "I'm having trouble connecting to the recommendation service. ";
      
      if (err.response) {
        const status = err.response.status;
        if (status === 400) {
          errorMessage = "Please provide a valid message. Try describing how you're feeling or what kind of movie you want.";
        } else if (status === 500) {
          errorMessage = "The recommendation service encountered an error. Please try again in a moment.";
        } else {
          errorMessage = `Server error (${status}). Please try again.`;
        }
      } else if (err.request) {
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

  const newChat = () => {
    const id = 'session_' + Math.random().toString(36).slice(2);
    setSessionId(id);
    localStorage.setItem('sessionId', id);
    setMessages([
      {
        type: 'bot',
        text: "New chat started. How are you feeling today? 🎬",
        timestamp: new Date()
      }
    ]);
    setError(null);
    setHighlightMovies([]);
    setHighlightDetails(null);
  };

  // Show panels when we have any recommendation; use 2-col until poster is loaded
  const haveRecs = Array.isArray(highlightMovies) && highlightMovies.length > 0;
  const showPanels = haveRecs || Boolean(highlightDetails);
  const layoutMode = posterReady ? 'three-col' : 'two-col';

  return (
    <div className="app">
      <Header onNewChat={newChat} currentSessionId={sessionId} />
      <Routes>
        <Route path="/chat" element={
          <div className={`main-layout ${showPanels ? layoutMode : 'single-col'}`}>
            {showPanels && (
              <div className="info-panel-col panel-animate panel-info">
                <InfoPanel
                  details={highlightDetails}
                  currentMovie={highlightMovies.length ? highlightMovies[highlightIndex] : null}
                />
              </div>
            )}
            {showPanels && (
              <div className={`left-panel poster-panel panel-animate panel-cover ${posterReady ? '' : 'poster-hidden'}`}>
                <HighlightPanel
                  hidden={!showHighlight}
                  onToggle={toggleHighlight}
                  currentMovie={highlightMovies.length ? highlightMovies[highlightIndex] : null}
                  details={highlightDetails}
                  loading={highlightLoading}
                  onPrev={handlePrevHighlight}
                  onNext={handleNextHighlight}
                  onPosterReady={(ready) => setPosterReady(!!ready)}
                />
              </div>
            )}
            <div className="right-panel chat-container">
              <div className="messages-container">
                {messages.map((message, index) => (
                  <ChatMessage key={index} message={message} onMovieSelect={handleMovieSelect} />
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
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  onKeyDown={handleKeyPress}
                  placeholder="Tell me how you're feeling or ask for a movie..."
                  className="chat-input"
                  disabled={isLoading}
                />
                <button type="submit" className="send-button" disabled={isLoading || !inputText.trim()}>
                  Send
                </button>
              </form>
              {error && <div className="error-banner">{error}</div>}
            </div>
          </div>
        } />
        <Route path="/" element={<About />} />
      </Routes>
      <Footer />
    </div>
  );
}

export default App;

