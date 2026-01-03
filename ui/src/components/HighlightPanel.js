import React, { useEffect, useState } from 'react';
import './HighlightPanel.css';

export default function HighlightPanel({ currentMovie, details, loading, onPrev, onNext, hidden, onToggle, onPosterReady }) {
  const [imgLoaded, setImgLoaded] = useState(false);
  const posterUrl = details?.poster_url;

  useEffect(() => {
    setImgLoaded(false);
    if (!posterUrl) return;
    const img = new Image();
    img.onload = () => setImgLoaded(true);
    img.src = posterUrl;
  }, [posterUrl]);
  useEffect(() => {
    if (typeof onPosterReady === 'function') {
      onPosterReady(posterUrl && imgLoaded);
    }
  }, [posterUrl, imgLoaded, onPosterReady]);

  return (
    <div className={`highlight-panel ${hidden ? 'collapsed' : ''}`}>
      {hidden ? (
        <div className="hp-collapsed-note">Panel hidden — toggle to show.</div>
      ) : (
        <div className="hp-content">
          {posterUrl && imgLoaded ? (
            <img className="hp-poster-large poster-enter" src={posterUrl} alt={`${details?.title || 'Movie'} poster`} />
          ) : null}
        </div>
      )}
    </div>
  );
}
