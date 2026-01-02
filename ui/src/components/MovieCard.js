import React from 'react';
import './MovieCard.css';

const MovieCard = ({ movie }) => {
  const genre = movie.genre || 'Unknown Genre';
  const title = movie.title || 'Untitled Movie';
  const year = movie.year || movie.releaseYear || '';

  return (
    <div className="movie-card">
      <div className="movie-header">
        <h4 className="movie-title">{title}</h4>
        {year && <span className="movie-year">{year}</span>}
      </div>
      <div className="movie-genre">
        <span className="genre-badge">{genre}</span>
      </div>
    </div>
  );
};

export default MovieCard;

