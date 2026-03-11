# AI-Powered Support Ticket Helper

An intelligent system that classifies support tickets, recommends KB articles, and identifies knowledge gaps using LLaMA, FAISS, and Sentence Transformers.

## Features

### 1. Ticket Classification
- **LLM-powered classification** using LLaMA models via Groq
- Automatically categorizes tickets into predefined categories
- Generates relevant tags and confidence scores
- Provides reasoning for classification decisions

### 2. KB Article Recommendations
- **Semantic search** using FAISS vector database
- Embeddings created with SentenceTransformer (all-MiniLM-L6-v2)
- Returns top-k most similar articles with similarity scores
- Fast and accurate recommendations

### 3. KB Gap Analysis
- Identifies low-performing articles (low CTR)
- Detects low-coverage articles (few views)
- Daily automated analysis with alerts
- Actionable insights for KB improvement

### 4. Sensitive Data Protection
- Automatic anonymization of:
  - Email addresses
  - Phone numbers
  - URLs
  - Credit card information
  - Transaction/Invoice IDs
  - API keys

## Tech Stack

- **Backend**: FastAPI (Python)
- **Frontend**: React + Tailwind CSS + Shadcn UI
- **LLM**: LLaMA via Groq (using Emergent LLM key)
- **Embeddings**: SentenceTransformers (all-MiniLM-L6-v2)
- **Vector DB**: FAISS
- **Dashboard**: Streamlit
- **Scheduling**: APScheduler
- **Database**: MongoDB (for future expansion)

## Project Structure

```
/app/
├── backend/
│   ├── data/
│   │   ├── tickets.csv          # Sample tickets
│   │   └── kb_articles.csv      # Sample KB articles
│   ├── index_data/
│   │   ├── kb_index.faiss       # FAISS index
│   │   └── kb_metadata.pkl      # Article metadata
│   ├── logs/                  # Alert logs
│   ├── preprocessing2.py      # Text cleaning & anonymization
│   ├── classification_tagging.py  # LLaMA classification
│   ├── build_index.py         # FAISS index builder
│   ├── recommend_api.py       # Recommendation engine
│   ├── csv_loader.py          # Data loader
│   ├── gap_analysis.py        # KB gap analyzer
│   ├── alert_logger.py        # Alert system
│   ├── scheduler.py           # Daily analysis scheduler
│   ├── server.py              # FastAPI server
│   ├── streamlit_dashboard.py # Streamlit dashboard
│   └── run_dashboard.sh       # Dashboard launcher
├── frontend/
│   └── src/
│       └── App.js             # React frontend
└── README.md
```

## API Endpoints

### Main Endpoints

1. **POST /api/analyze-ticket**
   - Full ticket analysis (preprocessing, classification, recommendations)
   - Request: `{"ticket_text": "string"}`
   - Response: Complete analysis with all components

2. **POST /api/recommend**
   - Get KB article recommendations
   - Request: `{"ticket_text": "string", "top_k": 3}`
   - Response: List of recommended articles with similarity scores

3. **POST /api/classify**
   - Classify ticket using LLaMA
   - Request: `{"ticket_text": "string"}`
   - Response: Category, tags, confidence, reasoning

4. **POST /api/preprocess**
   - Preprocess and anonymize text
   - Request: `{"ticket_text": "string"}`
   - Response: Original, cleaned, and anonymized text

5. **GET /api/gap-analysis**
   - Get KB gap analysis
   - Response: Summary, low performers, low coverage articles

6. **POST /api/build-index**
   - Build/rebuild FAISS index
   - Response: Status message

7. **GET /api/tickets**
   - Get all tickets from CSV

8. **GET /api/kb-articles**
   - Get all KB articles from CSV

## Usage

### 1. Build the FAISS Index

Before using recommendations, build the index:

```bash
cd /app/backend
python build_index.py
```

Or use the API:
```bash
curl -X POST http://localhost:8001/api/build-index
```

### 2. Analyze a Ticket

```bash
curl -X POST http://localhost:8001/api/analyze-ticket \
  -H "Content-Type: application/json" \
  -d '{"ticket_text": "My password reset link is not working"}'
```

### 3. Get Recommendations

```bash
curl -X POST http://localhost:8001/api/recommend \
  -H "Content-Type: application/json" \
  -d '{"ticket_text": "Cannot upload files", "top_k": 3}'
```

### 4. Run Gap Analysis

```bash
curl -X GET http://localhost:8001/api/gap-analysis
```

### 5. Launch Streamlit Dashboard

```bash
cd /app/backend
./run_dashboard.sh
```

Then open http://localhost:8501 in your browser.

### 6. Run Daily Scheduler (Optional)

```bash
cd /app/backend
python scheduler.py
```

## Frontend

The React frontend provides:
- Ticket analysis interface
- Real-time classification results
- KB article recommendations
- Gap analysis visualization
- Responsive design with Tailwind CSS

Access at: http://localhost:3000

## Streamlit Dashboard

The Streamlit dashboard offers:
- **Dashboard**: Overview metrics and performance stats
- **Analyze Ticket**: Interactive ticket analysis
- **KB Gap Analysis**: Detailed gap analysis with tables
- **Data Explorer**: Browse tickets and KB articles

Access at: http://localhost:8501

## Configuration

### Environment Variables

- `EMERGENT_LLM_KEY`: Universal API key for LLaMA (already configured)
- `MONGO_URL`: MongoDB connection string
- `DB_NAME`: Database name
- `CORS_ORIGINS`: Allowed CORS origins
- `REACT_APP_BACKEND_URL`: Backend URL for frontend

### Customization

- **Categories**: Edit in `classification_tagging.py`
- **CTR Threshold**: Adjust in `gap_analysis.py` (default: 20%)
- **Views Threshold**: Adjust in `gap_analysis.py` (default: 300)
- **Embedding Model**: Change in `build_index.py` and `recommend_api.py`
- **LLaMA Model**: Update in `classification_tagging.py`

## Sample Data

The system includes sample data:
- **10 support tickets** covering various categories
- **10 KB articles** with view/click analytics

Data files are in `/app/backend/data/`:
- `tickets.csv`
- `kb_articles.csv`

## Performance

- **Classification**: ~2-3 seconds per ticket (LLM call)
- **Recommendations**: <100ms per ticket (FAISS search)
- **Index Building**: ~5 seconds for 10 articles
- **Embedding Model**: 384 dimensions (all-MiniLM-L6-v2)

## Future Enhancements

1. **Google Sheets Integration**: Replace CSV with live Google Sheets
2. **Slack Alerts**: Add Slack webhook integration
3. **Advanced Analytics**: Add time-series analysis and trends
4. **Multi-language Support**: Support tickets in multiple languages
5. **Auto-response**: Generate suggested responses for tickets
6. **Batch Processing**: Process multiple tickets simultaneously
7. **User Feedback**: Allow users to rate recommendations
8. **A/B Testing**: Test different models and thresholds

## Troubleshooting

### Index Not Found Error
Run `python build_index.py` to create the FAISS index.

### LLM API Errors
Check that `EMERGENT_LLM_KEY` is set in `.env`.

### Dashboard Not Loading
Ensure backend is running on port 8001.

### Streamlit Connection Error
Verify `REACT_APP_BACKEND_URL` is correctly set.

## License

MIT License

## Support

For issues or questions, please check the logs in `/app/backend/logs/`.
