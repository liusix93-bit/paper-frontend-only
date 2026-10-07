# Paper Notion Agent

Upload a paper PDF, extract figures, summarize with DeepSeek, and push to a Notion database.

## Setup
1. `cp .env.example .env` and fill in your own keys (never commit `.env`).
2. Backend: `pip install -r backend/requirements.txt && cd backend && python main.py`
3. Frontend: `cd frontend && npm install && npm run dev`

## License

MIT
