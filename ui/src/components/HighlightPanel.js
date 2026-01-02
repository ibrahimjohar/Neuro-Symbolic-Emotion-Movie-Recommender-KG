import React from 'react';
import './HighlightPanel.css';

export default function HighlightPanel({ currentMovie, details, loading, onPrev, onNext, hidden, onToggle }) {
  return (
    <div className={`highlight-panel ${hidden ? 'collapsed' : ''}`}>
      {hidden ? (
        <div className="hp-collapsed-note">Panel hidden — toggle to show.</div>
      ) : (
        <div className="hp-content">
          {loading ? (
            <div className="hp-loading">Fetching poster…</div>
          ) : details && details.poster_url ? (
            <img className="hp-poster-large" src={details.poster_url} alt={`${details.title || 'Movie'} poster`} />
          ) : (
            <div className="hp-empty">Poster will appear after a recommendation.</div>
          )}
        </div>
      )}
    </div>
  );
}