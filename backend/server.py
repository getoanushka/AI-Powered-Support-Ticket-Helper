from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone

# Import custom modules (package-relative imports)
from .preprocessing2 import preprocess_ticket
from .classification_tagging import TicketClassifier
from .recommend_api import KBRecommender
from .gap_analysis import GapAnalyzer
from .csv_loader import CSVLoader

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Dashboard route: redirect to the Streamlit user dashboard
@app.get("/dashboard")
async def dashboard():
    return RedirectResponse(url="http://localhost:8501")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Initialize recommender (will be lazy loaded)
recommender = None

def get_recommender():
    global recommender
    if recommender is None:
        try:
            recommender = KBRecommender()
        except FileNotFoundError:
            # Index not built yet
            return None
    return recommender

# Models
class TicketRequest(BaseModel):
    ticket_text: str
    
class TicketAnalysisResponse(BaseModel):
    ticket_text: str
    preprocessed: dict
    classification: dict
    recommendations: List[dict]
    
class RecommendRequest(BaseModel):
    ticket_text: str
    top_k: Optional[int] = 3
    
class GapAnalysisResponse(BaseModel):
    summary: dict
    low_performers: List[dict]
    low_coverage: List[dict]

# Routes
@api_router.get("/")
async def root():
    return {"message": "AI Support Ticket Helper API"}

@api_router.post("/analyze-ticket", response_model=TicketAnalysisResponse)
async def analyze_ticket(request: TicketRequest):
    """
    Full ticket analysis: preprocessing, classification, and recommendations.
    """
    try:
        # Preprocess
        preprocessed = preprocess_ticket(request.ticket_text)
        
        # Classify
        classifier = TicketClassifier()
        classification = await classifier.classify_ticket(preprocessed['anonymized'])
        
        # Recommend
        rec = get_recommender()
        if rec:
            recommendations = rec.recommend(preprocessed['anonymized'], top_k=3)
        else:
            recommendations = []
        
        return {
            "ticket_text": request.ticket_text,
            "preprocessed": preprocessed,
            "classification": classification,
            "recommendations": recommendations
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/recommend")
async def recommend(request: RecommendRequest):
    """
    Get KB article recommendations for a ticket.
    """
    try:
        rec = get_recommender()
        if not rec:
            raise HTTPException(
                status_code=503, 
                detail="KB index not built. Please run build_index.py first."
            )
        
        recommendations = rec.recommend(request.ticket_text, top_k=request.top_k)
        
        return {
            "ticket_text": request.ticket_text,
            "recommendations": recommendations,
            "count": len(recommendations)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/classify")
async def classify(request: TicketRequest):
    """
    Classify a ticket using LLaMA/Groq.
    """
    try:
        classifier = TicketClassifier()
        result = await classifier.classify_ticket(request.ticket_text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/preprocess")
async def preprocess(request: TicketRequest):
    """
    Preprocess and anonymize ticket text.
    """
    try:
        result = preprocess_ticket(request.ticket_text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/gap-analysis", response_model=GapAnalysisResponse)
async def gap_analysis():
    """
    Perform KB gap analysis.
    """
    try:
        analyzer = GapAnalyzer()
        result = analyzer.analyze_gaps()
        
        return {
            "summary": result['summary'],
            "low_performers": result['low_performers'],
            "low_coverage": result['low_coverage']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/tickets")
async def get_tickets():
    """
    Get all tickets from CSV.
    """
    try:
        loader = CSVLoader()
        tickets = loader.get_tickets_as_dict()
        return {"tickets": tickets, "count": len(tickets)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/kb-articles")
async def get_kb_articles():
    """
    Get all KB articles from CSV.
    """
    try:
        loader = CSVLoader()
        articles = loader.get_kb_articles_as_dict()
        return {"articles": articles, "count": len(articles)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/build-index")
async def build_index_endpoint():
    """
    Build/rebuild the FAISS index.
    """
    try:
        # Use package-relative import so the endpoint works when running as a module
        from .build_index import KBIndexBuilder
        builder = KBIndexBuilder()
        csv_path = ROOT_DIR / 'data' / 'kb_articles.csv'
        builder.build_and_save(str(csv_path))
        
        # Reload recommender
        global recommender
        recommender = None
        get_recommender()
        
        return {"status": "success", "message": "Index built successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

@app.on_event("startup")
async def startup_event():
    logger.info("AI Support Ticket Helper API started")
    # Try to load recommender on startup
    try:
        get_recommender()
        logger.info("KB Recommender loaded successfully")
    except:
        logger.warning("KB Recommender not available. Run /api/build-index to initialize.")