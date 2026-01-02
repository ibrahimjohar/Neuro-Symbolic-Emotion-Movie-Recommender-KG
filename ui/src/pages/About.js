import React from 'react';

const About = () => {
  return (
    <div style={{ padding: '20px' }}>
      <h2 style={{ color: '#000000', marginBottom: '10px' }}>About</h2>
      <p style={{ color: '#333', lineHeight: 1.6 }}>
        This emotion-aware movie recommender blends a lightweight ML signal with a semantic knowledge graph to suggest films that match your mood and preferences.
      </p>
      <ul style={{ color: '#333', lineHeight: 1.8, marginTop: '10px' }}>
        <li>Black/grey/white minimal UI theme</li>
        <li>Context-aware recommendations using per-session signals</li>
        <li>Comfort-focused filtering to avoid harsh genres when requested</li>
        <li>Novelty prioritization to reduce repeats</li>
      </ul>
      <p style={{ color: '#333', marginTop: '12px' }}>
        Use the New Chat button in the header to start a fresh session, or continue chatting to refine recommendations.
      </p>
    </div>
  );
};

export default About;