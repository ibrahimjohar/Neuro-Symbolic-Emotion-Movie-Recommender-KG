import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import './Header.css';

const Header = ({ onNewChat, currentSessionId }) => {
  const location = useLocation();
  const isActive = (path) => location.pathname === path;

  const shortSession = currentSessionId ? currentSessionId.replace('session_', '').slice(0, 6) : '—';

  return (
    <header className="site-header">
      <div className="header-inner">
        <div className="header-left">
          <Link to="/" className="brand">Emotion Movie Recommender</Link>
          <nav className="nav">
            <Link to="/" className={`nav-link ${isActive('/') ? 'active' : ''}`}>Chat</Link>
            <Link to="/about" className={`nav-link ${isActive('/about') ? 'active' : ''}`}>About</Link>
          </nav>
        </div>
        <div className="header-right">
          <div className="session-indicator" title={`Session: ${currentSessionId || ''}`}>Session: {shortSession}</div>
          <button className="new-chat-button" onClick={onNewChat} title="Start a new chat">New Chat</button>
        </div>
      </div>
    </header>
  );
};

export default Header;