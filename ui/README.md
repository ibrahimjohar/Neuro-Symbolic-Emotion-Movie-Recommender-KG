# Emotion Movie Recommender Chatbot

A React-based chatbot interface for the Neuro-Symbolic Emotion Movie Recommender API.

## Features

- 🎬 Real-time chat interface
- 🎭 Emotion-aware movie recommendations
- 📱 Responsive design
- ⚡ Fast API integration
- 🎨 Beautiful UI with smooth animations
- 🛡️ Comprehensive error handling
- 📊 Movie cards with title, year, and genre

## Setup

1. Install dependencies:
```bash
cd ui
npm install
```

2. Make sure your FastAPI server is running on `http://localhost:8000`

3. Start the React app:
```bash
npm start
```

The app will open at `http://localhost:3000`

## Usage

1. Type how you're feeling or what kind of movie you want
2. The bot will analyze your emotions and recommend movies
3. View recommended movies with their genres
4. Continue the conversation to get more recommendations

## API Integration

The chatbot connects to the `/chat` endpoint:
- Endpoint: `http://localhost:8000/chat`
- Method: POST
- Request body: `{ text, user_id, threshold, top_k }`
- Response: `{ reply, movies, genre_scores, ml_scores }`

## Error Handling

The chatbot handles:
- Network errors
- API timeouts
- Server errors (400, 500, etc.)
- Empty responses
- Connection failures

## Build for Production

```bash
npm run build
```

This creates an optimized build in the `build/` folder.

