# Quick Start Guide

## AI Support Ticket Helper - Quick Start

### What You've Built

An AI-powered system that:
1. **Classifies** support tickets using LLaMA models
2. **Recommends** relevant KB articles using FAISS vector search
3. **Identifies** knowledge gaps in your documentation
4. **Anonymizes** sensitive customer data automatically

### Access Points

#### 1. Main Web App (React)
**URL:** http://localhost:3000

**Features:**
- Analyze support tickets
- View classification results
- Get KB article recommendations
- Browse gap analysis

#### 2. Streamlit Dashboard
**URL:** http://localhost:8501
**Launch:** `cd /app/backend && ./run_dashboard.sh`

**Features:**
- Interactive ticket analysis
- Detailed analytics dashboard
- KB performance metrics
- Data explorer

#### 3. API Endpoints
**Base URL:** http://localhost:8001/api

**Key Endpoints:**
- `POST /analyze-ticket` - Full ticket analysis
- `POST /recommend` - Get KB recommendations
- `GET /gap-analysis` - KB performance analysis
- `POST /build-index` - Rebuild FAISS index

### Quick Test

#### Test 1: Analyze a Ticket (Web UI)
1. Go to http://localhost:3000
2. Enter this ticket: "My password reset link is not working. I clicked it multiple times."
3. Click "Analyze Ticket"
4. See classification, tags, and KB recommendations

#### Test 2: API Test (Terminal)
```bash
API_URL=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d '=' -f2)

# Analyze a ticket
curl -X POST "$API_URL/api/analyze-ticket" \
  -H "Content-Type: application/json" \
  -d '{"ticket_text": "Cannot upload files larger than 10MB"}'

# Get gap analysis
curl -X GET "$API_URL/api/gap-analysis"
```

#### Test 3: View Sample Data
```bash
# View tickets
cat /app/backend/data/tickets.csv

# View KB articles
cat /app/backend/data/kb_articles.csv
```

### How It Works

#### 1. Preprocessing
- Cleans ticket text
- Anonymizes sensitive data (emails, phones, URLs, cards, API keys)
- Returns both original and anonymized versions

#### 2. Classification (LLaMA)
- Uses Groq API with LLaMA models
- Classifies into categories (Authentication, Payment, API, etc.)
- Generates relevant tags
- Provides confidence score

#### 3. Recommendations (FAISS)
- Converts ticket to embedding (384D vector)
- Searches FAISS index for similar KB articles
- Returns top-3 matches with similarity scores

#### 4. Gap Analysis
- Calculates CTR (Click-Through Rate) for each article
- Identifies low-performing articles (CTR < 20%)
- Identifies low-coverage articles (views < 300)
- Provides actionable insights

### Customization

#### Add Your Own Data

**Tickets:** Edit `/app/backend/data/tickets.csv`
```csv
ticket_id,ticket_text,category,created_at
TKT011,"Your ticket text here",Category,2025-01-17 10:00:00
```

**KB Articles:** Edit `/app/backend/data/kb_articles.csv`
```csv
article_id,title,content,category,views,clicks
KB011,"Article Title","Article content...",Category,100,20
```

**Rebuild Index:** After updating data
```bash
cd /app/backend
python build_index.py
```

#### Change LLM Model

Edit `/app/backend/classification_tagging.py`:
```python
# Current: gpt-5.1 (via Emergent LLM key)
chat.with_model("openai", "gpt-5.1")

# Change to different model if needed
```

#### Adjust Thresholds

Edit `/app/backend/gap_analysis.py`:
```python
# CTR threshold (default: 20%)
def identify_low_performers(self, df, ctr_threshold=0.2):

# Views threshold (default: 300)
def identify_low_coverage(self, df, views_threshold=300):
```

### Architecture

```
Ticket Input
    ↓
[Preprocessing]
    ↓
[LLaMA Classification] → Category, Tags, Confidence
    ↓
[SentenceTransformer] → Embedding (384D)
    ↓
[FAISS Search] → Top-K Similar Articles
    ↓
Recommendations
```

### Daily Automation (Optional)

To run gap analysis daily:

```bash
cd /app/backend
python scheduler.py
```

This will:
- Run analysis every 24 hours
- Log results to `/app/backend/logs/`
- Alert on KB performance issues

### Troubleshooting

**Issue:** "Index not found" error
**Fix:** Run `cd /app/backend && python build_index.py`

**Issue:** Classification not working
**Fix:** Check EMERGENT_LLM_KEY in `/app/backend/.env`

**Issue:** Frontend not loading
**Fix:** Ensure backend is running on port 8001

**Issue:** Streamlit dashboard not accessible
**Fix:** Run `cd /app/backend && ./run_dashboard.sh`

### Sample Output

#### Classification Result:
```json
{
  "category": "Authentication",
  "tags": ["password-reset", "login-issue", "email-link"],
  "confidence": 0.96,
  "status": "success"
}
```

#### Recommendation Result:
```json
{
  "article_id": "KB001",
  "title": "How to Reset Your Password",
  "similarity_score": 0.63,
  "rank": 1
}
```

#### Gap Analysis Result:
```json
{
  "summary": {
    "total_articles": 10,
    "avg_ctr": 0.303,
    "low_performers_count": 0,
    "low_coverage_count": 2
  }
}
```

### Next Steps

1. **Add Real Data**: Replace sample CSVs with your actual tickets and KB articles
2. **Integrate Google Sheets**: Implement live data loading from Google Sheets
3. **Add Slack Alerts**: Configure Slack webhook for automated alerts
4. **Monitor Performance**: Track classification accuracy and recommendation relevance
5. **Iterate**: Use gap analysis insights to improve your KB

### Resources

- Full Documentation: `/app/README.md`
- Sample Data: `/app/backend/data/`
- API Endpoints: http://localhost:8001/docs (FastAPI auto-docs)
- Backend Code: `/app/backend/`
- Frontend Code: `/app/frontend/src/`

### Support

For issues or questions:
- Check logs: `/app/backend/logs/`
- Check backend logs: `tail -f /var/log/supervisor/backend.err.log`
- Check frontend logs: `tail -f /var/log/supervisor/frontend.err.log`
