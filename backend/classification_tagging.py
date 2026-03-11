import os
import json
import asyncio
from typing import Dict, List
from dotenv import load_dotenv

# Try to import emergentintegrations (preferred LLaMA/Groq integration).
try:
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    _HAS_EMERGENT = True
except Exception:
    _HAS_EMERGENT = False

    class UserMessage:
        def __init__(self, text: str):
            self.text = text

    class LlmChat:
        def __init__(self, *args, **kwargs):
            pass

        def with_model(self, *args, **kwargs):
            return self

        async def send_message(self, user_message: UserMessage):
            import json as _json
            # Return a safe default JSON classification when no LLM available
            return _json.dumps({
                "category": "Other",
                "tags": ["support"],
                "confidence": 0.5,
                "reasoning": "Fallback classifier (no LLM provider configured)"
            })

load_dotenv()

# Additionally support OpenAI as a fallback provider when emergent isn't available.
try:
    import openai
    _HAS_OPENAI = True
except Exception:
    _HAS_OPENAI = False

# If no external LLM is available, provide an embedding-based classifier
try:
    from sentence_transformers import SentenceTransformer
    import numpy as _np
    import pandas as _pd
    _HAS_EMBEDDING_CLASSIFIER = True
except Exception:
    _HAS_EMBEDDING_CLASSIFIER = False


class EmbeddingClassifier:
    """
    Lightweight classifier that infers category and tags by matching ticket
    embeddings to KB article embeddings. This works offline using
    `all-MiniLM-L6-v2` and the repository `backend/data/kb_articles.csv`.
    """
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        if not _HAS_EMBEDDING_CLASSIFIER:
            raise RuntimeError('sentence-transformers not available')

        self.model = SentenceTransformer(model_name)
        # Load KB articles from disk
        from pathlib import Path
        kb_csv = Path(__file__).parent / 'data' / 'kb_articles.csv'
        if not kb_csv.exists():
            self.articles_df = _pd.DataFrame()
            self.embeddings = _np.zeros((0, 384), dtype='float32')
            return

        self.articles_df = _pd.read_csv(kb_csv)
        texts = (self.articles_df['title'].fillna('') + '. ' + self.articles_df['content'].fillna('')).tolist()
        self.embeddings = self.model.encode(texts, convert_to_numpy=True)

    def classify(self, ticket_text: str, top_k: int = 3) -> Dict:
        if self.embeddings.size == 0:
            return {
                'category': 'Other',
                'tags': ['support'],
                'confidence': 0.5,
                'reasoning': 'No KB articles available for embedding-based classification',
                'status': 'success'
            }

        ticket_emb = self.model.encode([ticket_text], convert_to_numpy=True)[0]
        # cosine similarity
        def cosine(a, b):
            return _np.dot(a, b) / (_np.linalg.norm(a) * _np.linalg.norm(b) + 1e-10)

        sims = [_np.dot(ticket_emb, v) / (_np.linalg.norm(ticket_emb) * (_np.linalg.norm(v) + 1e-10)) for v in self.embeddings]
        sims = _np.array(sims)
        top_idx = sims.argsort()[::-1][:top_k]
        # derive category by majority vote among top articles
        top_categories = self.articles_df.iloc[top_idx]['category'].fillna('Other').tolist()
        from collections import Counter
        cat_counts = Counter(top_categories)
        category = cat_counts.most_common(1)[0][0] if len(cat_counts) > 0 else 'Other'

        # tags: extract keywords from titles of top articles (simple split)
        tags = []
        for i in top_idx:
            title = str(self.articles_df.iloc[i]['title'])
            for w in title.lower().split():
                w = w.strip('.,()"\'')
                if len(w) > 3 and w not in tags:
                    tags.append(w)
                if len(tags) >= 5:
                    break
            if len(tags) >= 5:
                break

        # confidence: map top similarity to 0-1
        top_sim = float(sims[top_idx[0]]) if len(top_idx) > 0 else 0.0
        # normalize typical sentence-transformer cosine (~0.3-0.8) to 0-1
        conf = max(0.0, min(1.0, (top_sim - 0.2) / (0.6)))

        reasoning = f"Embedding match to top article(s): {', '.join(self.articles_df.iloc[top_idx]['title'].tolist())}"

        return {
            'category': category,
            'tags': tags[:5],
            'confidence': conf,
            'reasoning': reasoning,
            'status': 'success'
        }

class TicketClassifier:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('EMERGENT_LLM_KEY')
        
    async def classify_ticket(self, ticket_text: str) -> Dict:
        """
        Classify a ticket using Groq LLaMA model.
        Returns category, tags, and confidence score.
        """
        # Build classification prompt
        prompt = f"""Analyze this support ticket and classify it.

Ticket: {ticket_text}

Provide a JSON response with:
- category: One of [Authentication, Access, Payment, Data Export, Performance, File Upload, API, Integration, Billing, Other]
- tags: Array of relevant tags (2-5 tags)
- confidence: Float between 0 and 1
- reasoning: Brief explanation

Respond ONLY with valid JSON, no additional text."""

        # Prefer emergentintegrations LLM if available
        if _HAS_EMERGENT:
            try:
                chat = LlmChat(
                    api_key=self.api_key,
                    session_id="ticket-classifier",
                    system_message="You are a support ticket classification assistant. Analyze tickets and return structured JSON with category, tags, and confidence."
                )
                # choose the LLaMA model if configured via env
                model_name = os.getenv('EMERGENT_MODEL', 'llama-3.1-8b-instant')
                chat.with_model('emergent', model_name)
                user_message = UserMessage(text=prompt)
                response = await chat.send_message(user_message)
                result = json.loads(response)
                return {
                    'category': result.get('category', 'Other'),
                    'tags': result.get('tags', []),
                    'confidence': result.get('confidence', 0.5),
                    'reasoning': result.get('reasoning', ''),
                    'status': 'success'
                }
            except Exception as e:
                # fall through to other providers
                pass

        # If an Emergent HTTP API is configured, call it (generic adapter)
        if os.getenv('EMERGENT_API_URL') and os.getenv('EMERGENT_LLM_KEY'):
            try:
                try:
                    from .emergent_adapter import EmergentAdapter
                except Exception:
                    from emergent_adapter import EmergentAdapter

                import asyncio as _asyncio

                def _call_emerg():
                    adapter = EmergentAdapter()
                    return adapter.send(prompt, model=os.getenv('EMERGENT_MODEL'))

                resp_text = await _asyncio.get_event_loop().run_in_executor(None, _call_emerg)
                # Try to parse JSON response; be permissive
                try:
                    result = json.loads(resp_text)
                except Exception:
                    import re
                    m = re.search(r"\{.*\}", resp_text, re.S)
                    if m:
                        try:
                            result = json.loads(m.group(0))
                        except Exception:
                            result = None
                    else:
                        result = None

                if result:
                    return {
                        'category': result.get('category', 'Other'),
                        'tags': result.get('tags', []),
                        'confidence': result.get('confidence', 0.5),
                        'reasoning': result.get('reasoning', resp_text),
                        'status': 'success'
                    }
                else:
                    # Return the raw text in reasoning when parse fails
                    return {
                        'category': 'Other',
                        'tags': ['support'],
                        'confidence': 0.5,
                        'reasoning': resp_text,
                        'status': 'success'
                    }
            except Exception:
                # fall through to other providers
                pass

        # Fallback to OpenAI if configured
        if _HAS_OPENAI and os.getenv('OPENAI_API_KEY'):
            try:
                openai.api_key = os.getenv('OPENAI_API_KEY')
                # Use ChatCompletion synchronously in executor to avoid blocking
                import asyncio as _asyncio

                def _call_openai():
                    resp = openai.ChatCompletion.create(
                        model=os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),
                        messages=[
                            {"role": "system", "content": "You are a support ticket classification assistant. Return ONLY a JSON object with category, tags, confidence (0-1), and reasoning."},
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=300,
                        temperature=0.0
                    )
                    return resp

                resp = await _asyncio.get_event_loop().run_in_executor(None, _call_openai)
                # Extract content
                text = resp['choices'][0]['message']['content']
                result = json.loads(text)
                return {
                    'category': result.get('category', 'Other'),
                    'tags': result.get('tags', []),
                    'confidence': result.get('confidence', 0.5),
                    'reasoning': result.get('reasoning', ''),
                    'status': 'success'
                }
            except Exception:
                pass

        # Final fallback: use offline embedding-based classifier if available
        if _HAS_EMBEDDING_CLASSIFIER:
            try:
                import asyncio as _asyncio

                def _run_emb():
                    ec = EmbeddingClassifier()
                    return ec.classify(ticket_text)

                result = await _asyncio.get_event_loop().run_in_executor(None, _run_emb)
                return result
            except Exception:
                pass

        # Last-resort safe response
        return {
            'category': 'Other',
            'tags': ['support'],
            'confidence': 0.5,
            'reasoning': 'Fallback classifier (no LLM provider configured or error occurred)',
            'status': 'success'
        }

async def classify_ticket_batch(tickets: List[str]) -> List[Dict]:
    """
    Classify multiple tickets.
    """
    classifier = TicketClassifier()
    results = []
    
    for ticket in tickets:
        result = await classifier.classify_ticket(ticket)
        results.append(result)
    
    return results