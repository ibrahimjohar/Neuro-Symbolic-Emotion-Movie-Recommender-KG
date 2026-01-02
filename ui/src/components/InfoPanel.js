import React from 'react';
import './InfoPanel.css';

export default function InfoPanel({ details, currentMovie }) {
  const title = details?.title || currentMovie?.title || 'TITLE';
  const year = details?.year || currentMovie?.year || '';
  const overview = details?.overview || 'Long paragraph of details will appear here when available. It includes a short synopsis and helpful context so you can decide quickly.';
  const rating = details?.rating ? `${details.rating}/10` : null;
  const genres = Array.isArray(details?.genres) ? details.genres : [];

  return (
    <div className="info-panel">
      <h1 className="info-title">{title}{year ? ` (${year})` : ''}</h1>
      <div className="info-sub">DETAILS</div>
      {rating && <div className="info-meta">Rating: {rating}</div>}
      {genres.length > 0 && (
        <div className="info-genres">
          {genres.slice(0, 6).map((g, i) => (
            <span key={i} className="info-genre-pill">{g}</span>
          ))}
        </div>
      )}
      <p className="info-overview">{overview}</p>
    </div>
  );
}