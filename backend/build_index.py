import os
import pickle
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
import faiss
from pathlib import Path
from typing import Dict, List

class KBIndexBuilder:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize index builder with sentence transformer model.
        """
        print(f"Loading sentence transformer model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.dimension = 384  # all-MiniLM-L6-v2 embedding dimension
        
    def load_kb_articles(self, csv_path: str) -> pd.DataFrame:
        """
        Load KB articles from CSV.
        """
        df = pd.read_csv(csv_path)
        return df
    
    def create_embeddings(self, articles_df: pd.DataFrame) -> np.ndarray:
        """
        Create embeddings for KB articles.
        Combines title and content for better semantic search.
        """
        # Combine title and content
        texts = []
        for _, row in articles_df.iterrows():
            text = f"{row['title']}. {row['content']}"
            texts.append(text)
        
        print(f"Creating embeddings for {len(texts)} articles...")
        embeddings = self.model.encode(texts, show_progress_bar=True)
        
        return embeddings
    
    def build_faiss_index(self, embeddings: np.ndarray) -> faiss.IndexFlatL2:
        """
        Build FAISS index from embeddings.
        """
        print("Building FAISS index...")
        index = faiss.IndexFlatL2(self.dimension)
        index.add(embeddings.astype('float32'))
        print(f"Index built with {index.ntotal} vectors")
        
        return index
    
    def save_index(self, index: faiss.IndexFlatL2, metadata: Dict, 
                   index_path: str, metadata_path: str):
        """
        Save FAISS index and metadata to disk.
        """
        # Create directory if not exists
        os.makedirs(os.path.dirname(index_path), exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(index, index_path)
        print(f"FAISS index saved to {index_path}")
        
        # Save metadata
        with open(metadata_path, 'wb') as f:
            pickle.dump(metadata, f)
        print(f"Metadata saved to {metadata_path}")
    
    def build_and_save(self, csv_path: str, output_dir: str | Path = None):
        """
        Full pipeline: load articles, create embeddings, build index, save.
        """
        if output_dir is None:
            output_dir = Path(__file__).resolve().parent / 'index_data'
        output_dir = Path(output_dir)

        # Load articles
        articles_df = self.load_kb_articles(csv_path)
        
        # Create embeddings
        embeddings = self.create_embeddings(articles_df)
        
        # Build FAISS index
        index = self.build_faiss_index(embeddings)
        
        # Prepare metadata
        metadata = {
            'article_ids': articles_df['article_id'].tolist(),
            'titles': articles_df['title'].tolist(),
            'categories': articles_df['category'].tolist(),
            'contents': articles_df['content'].tolist()
        }
        
        # Save
        index_path = output_dir / 'kb_index.faiss'
        metadata_path = output_dir / 'kb_metadata.pkl'
        self.save_index(index, metadata, str(index_path), str(metadata_path))
        
        return index, metadata

if __name__ == '__main__':
    builder = KBIndexBuilder()
    base_dir = Path(__file__).resolve().parent
    csv_path = base_dir / 'data' / 'kb_articles.csv'
    builder.build_and_save(csv_path)