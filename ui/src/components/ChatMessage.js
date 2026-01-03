import React from 'react';
import MovieCard from './MovieCard';
import './ChatMessage.css';

const ChatMessage = ({ message, onMovieSelect }) => {
  const isBot = message.type === 'bot';
  const isError = message.isError;

  return (
    <div className={`message ${isBot ? 'bot-message' : 'user-message'} ${isError ? 'error-message' : ''}`}>
      <div className="message-content">
        <div className="message-text">
          {message.text}
        </div>
        
        {isBot && message.movies && message.movies.length > 0 && (
          <div className="movies-section">
            <div className="movies-header">
              <h3>🎬 Recommended Movies</h3>
              {message.genreScores && message.genreScores.length > 0 && (
                <div className="genre-tags">
                  {message.genreScores.slice(0, 3).map((genre, idx) => (
                    <span key={idx} className="genre-tag">
                      {genre.genre_uri?.replace('emo:', '').replace('_genre', '').replace(/([A-Z])/g, ' $1').trim() || 'Genre'}
                    </span>
                  ))}
                </div>
              )}
            </div>
            <div className="movies-grid">
              {message.movies.slice(0, 5).map((movie, index) => (
                <MovieCard
                  key={index}
                  movie={movie}
                  onClick={(m) => onMovieSelect && onMovieSelect(m, index, message.movies)}
                />
              ))}
            </div>
          </div>
        )}

        {isBot && message.movies && message.movies.length === 0 && !isError && message.genreScores && message.genreScores.length > 0 && (
          <div className="no-movies">
            <p>I couldn't find specific movies, but I detected these genre preferences:</p>
            {message.genreScores && message.genreScores.length > 0 && (
              <div className="genre-tags">
                {message.genreScores.map((genre, idx) => (
                  <span key={idx} className="genre-tag">
                    {genre.genre_uri?.replace('emo:', '').replace('_genre', '').replace(/([A-Z])/g, ' $1').trim() || 'Genre'}
                  </span>
                ))}
              </div>
            )}
          </div>
        )}

        <div className="message-time">
          {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </div>
      </div>
    </div>
  );
};

export default ChatMessage;

