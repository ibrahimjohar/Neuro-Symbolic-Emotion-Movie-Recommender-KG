import React from 'react';
import './HighlightPanel.css';

export default function HighlightPanel({ currentMovie, details, loading, onPrev, onNext, hidden, onToggle }) {
  return (
    <div className={`highlight-panel ${hidden ? 'collapsed' : ''}`}>
      <div className="hp-header">
        <span className="hp-title">Highlighted Film</span>
        <div className="hp-actions">
          <button className="hp-btn" onClick={onPrev} title="Previous">◀</button>
          <button className="hp-btn" onClick={onNext} title="Next">▶</button>
          <button className="hp-btn hp-toggle" onClick={onToggle} title={hidden ? 'Show panel' : 'Hide panel'}>
            {hidden ? 'Show' : 'Hide'}
          </button>
        </div>
      </div>

      {hidden ? (
        <div className="hp-collapsed-note">Panel hidden — toggle to show.</div>
      ) : (
        <div className="hp-content">
          {loading ? (
            <div className="hp-loading">Fetching film details…</div>
          ) : details ? (
            <div className="hp-card">
              {details.poster_url && (
                <img className="hp-poster" src={details.poster_url} alt={`${details.title} poster`} />
              )}
              <div className="hp-info">
                <div className="hp-main">
                  <div className="hp-titleline">
                    <span className="hp-name">{details.title}</span>
                    {details.year && <span className="hp-year">{details.year}</span>}
                  </div>
                  {details.rating !== undefined && (
                    <div className="hp-rating">Rating: {Number(details.rating).toFixed(1)}</div>
                  )}
                </div>
                {Array.isArray(details.genres) && details.genres.length > 0 && (
                  <div className="hp-genres">
                    {details.genres.map((g) => (
                      <span key={g} className="hp-genre-pill">{g}</span>
                    ))}
                  </div>
                )}
                {Array.isArray(details.cast) && details.cast.length > 0 && (
                  <div className="hp-cast">
                    <div className="hp-cast-label">Cast</div>
                    <div className="hp-cast-list">{details.cast.join(', ')}</div>
                  </div>
                )}
                {details.overview && (
                  <div className="hp-overview">{details.overview}</div>
                )}
                {details.tmdb_id && (
                  <a
                    className="hp-link"
                    href={`https://www.themoviedb.org/movie/${details.tmdb_id}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    title="View on TMDb"
                  >
                    View on TMDb ↗
                  </a>
                )}
              </div>
            </div>
          ) : currentMovie ? (
            <div className="hp-placeholder">
              <div className="hp-placeholder-title">{currentMovie.title}</div>
              {currentMovie.year && <div className="hp-placeholder-year">{currentMovie.year}</div>}
              <div className="hp-placeholder-note">No external details available.</div>
            </div>
          ) : (
            <div className="hp-empty">Ask for recommendations to see a highlight here.</div>
          )}
        </div>
      )}
    </div>
  );
}