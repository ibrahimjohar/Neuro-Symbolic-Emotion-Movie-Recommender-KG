import React from 'react';
import { Link } from 'react-router-dom';
import './About.css';

const About = () => {
  return (
    <div className="about-page">
      <section className="about-hero">
        <h1 className="about-title">Neuro‑Symbolic‑Emotion‑Aware Movie Recommender</h1>
        <p className="about-subtitle">A neuro‑symbolic recommender that blends lightweight ML signals with a semantic knowledge graph.</p>
        <div className="about-actions">
          <Link to="/chat" className="about-cta">Start Chat</Link>
        </div>
      </section>

      <section className="about-grid">
        <div className="about-card">
          <h3 className="about-card-title">Overview</h3>
          <p className="about-card-text">Suggests films that align with how you feel and what you prefer, then presents details, posters, and genres in a focused UI.</p>
        </div>
        <div className="about-card">
          <h3 className="about-card-title">Project Flow</h3>
          <ul className="about-list">
            <li>User enters a mood or preference in chat</li>
            <li>Backend infers emotions and updates per‑session context</li>
            <li>Ontology mapping selects relevant genre classes</li>
            <li>SPARQL queries fetch candidate movies from the KG</li>
            <li>Candidates are ranked and refined; details are fetched from TMDb</li>
          </ul>
        </div>
        <div className="about-card">
          <h3 className="about-card-title">Tech Stack</h3>
          <ul className="about-list">
            <li>Frontend: React 18, React Router, Axios, CSS</li>
            <li>Backend: Python 3, FastAPI, requests</li>
            <li>Knowledge Graph: Apache Jena Fuseki, RDF/TTL</li>
            <li>Integration: TMDb for details and posters</li>
          </ul>
        </div>
        <div className="about-card">
          <h3 className="about-card-title">Credits</h3>
          <p className="about-card-text">© Neuro‑Symbolic‑Emotion‑Aware Movie Recommender</p>
        </div>
      </section>
    </div>
  );
};

export default About;
