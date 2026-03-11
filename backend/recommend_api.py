import os
import pickle
import numpy as np
try:
    import faiss
    _HAS_FAISS = True
except Exception:
    faiss = None
    _HAS_FAISS = False

try:
    from sentence_transformers import SentenceTransformer
    _HAS_SENTENCE_TRANSFORMERS = True
except Exception:
    SentenceTransformer = None
    _HAS_SENTENCE_TRANSFORMERS = False
from typing import List, Dict
from pathlib import Path

class KBRecommender:
    def __init__(self, index_dir: str = None):
        # default to repository-relative backend/index_data
        if index_dir:
            self.index_dir = index_dir
        else:
            from pathlib import Path
            self.index_dir = str(Path(__file__).parent / 'index_data')

        """
        Initialize recommender with pre-built FAISS index.
        """
        # Use SentenceTransformer if available, otherwise a lightweight fallback
        if _HAS_SENTENCE_TRANSFORMERS and SentenceTransformer is not None:
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
        else:
            class _FallbackModel:
                def encode(self, texts):
                    # deterministic lightweight embedding: convert chars to mean ord value
                    embs = []
                    for t in texts:
                        if not t:
                            embs.append(np.zeros(384, dtype='float32'))
                            continue
                        vals = [ord(c) for c in t[:1024]]
                        arr = np.array(vals, dtype='float32')
                        if arr.size == 0:
                            embs.append(np.zeros(384, dtype='float32'))
                        else:
                            v = np.mean(arr) / 256.0
                            vec = np.full(384, v, dtype='float32')
                            embs.append(vec)
                    return np.vstack(embs)

            self.model = _FallbackModel()
        self.index = None
        self.metadata = None
        
        try:
            self._load_index()
        except Exception:
            # If FAISS or index isn't available, keep a safe fallback
            self.index = None
            self.metadata = None
            return
    
    def _load_index(self):
        """
        Load FAISS index and metadata from disk.
        """
        index_path = os.path.join(self.index_dir, 'kb_index.faiss')
        metadata_path = os.path.join(self.index_dir, 'kb_metadata.pkl')
        
        if not os.path.exists(index_path) or not os.path.exists(metadata_path):
            raise FileNotFoundError(
                f"Index files not found in {self.index_dir}. "
                "Please run build_index.py first."
            )
        
        # Load FAISS index
        self.index = faiss.read_index(index_path)
        
        # Load metadata
        with open(metadata_path, 'rb') as f:
            self.metadata = pickle.load(f)
        
        print(f"Loaded index with {self.index.ntotal} articles")
    
    def recommend(self, ticket_text: str, top_k: int = 3) -> List[Dict]:
        """
        Recommend top-k KB articles for a ticket.
        """
        # If index not available, return empty recommendations
        if self.index is None:
            return []

        # Create embedding for ticket
        ticket_embedding = self.model.encode([ticket_text])
        
        # Search FAISS index
        distances, indices = self.index.search(
            ticket_embedding.astype('float32'), 
            top_k
        )
        
        # Prepare recommendations
        recommendations = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.metadata['article_ids']):
                similarity_score = 1 / (1 + distances[0][i])  # Convert distance to similarity
                
                recommendations.append({
                    'article_id': self.metadata['article_ids'][idx],
                    'title': self.metadata['titles'][idx],
                    'category': self.metadata['categories'][idx],
                    'content': self.metadata['contents'][idx],
                    'similarity_score': float(similarity_score),
                    'rank': i + 1
                })
        
        return recommendations