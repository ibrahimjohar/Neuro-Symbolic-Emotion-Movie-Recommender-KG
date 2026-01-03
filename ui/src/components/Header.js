import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import './Header.css';

const Header = ({ onNewChat, currentSessionId }) => {
  const location = useLocation();
  const isActive = (path) => location.pathname === path;

  // session indicator removed per request

  return (
    <header className="site-header">
      <div className="header-inner">
        <div className="header-left">
          <Link to="/" className="brand">Neuro‑Symbolic‑Emotion‑Aware Movie Recommender</Link>
          <nav className="nav">
            <Link to="/" className={`nav-link ${isActive('/') ? 'active' : ''}`}>Home</Link>
            <Link to="/chat" className={`nav-link ${isActive('/chat') ? 'active' : ''}`}>Chat</Link>
          </nav>
        </div>
        <div className="header-right">
          <button className="new-chat-button" onClick={onNewChat} title="Start a new chat">New Chat</button>
        </div>
      </div>
    </header>
  );
};

export default Header;
