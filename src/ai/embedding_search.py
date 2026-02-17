import logging
import time
from typing import List, Dict, Any, Tuple
import numpy as np
try:
    from sentence_transformers import SentenceTransformer, util
    import torch
except ImportError:
    SentenceTransformer = None
    torch = None

logger = logging.getLogger("tnea_ai.ai.embedding")

class CollegeEmbeddingSearch:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CollegeEmbeddingSearch, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        self.model = None
        self.college_embeddings = None
        self.college_names = []
        self.college_codes = []
        self.colleges_data = [] # Keep reference to full objects
        
        self.model_name = 'all-MiniLM-L6-v2'
        self._load_model()
        self._initialized = True

    def _load_model(self):
        """Loads the sentence-transformer model."""
        if SentenceTransformer is None:
            logger.error("sentence-transformers not installed. Semantic search disabled.")
            return

        try:
            logger.info(f"Loading embedding model: {self.model_name}...")
            start_time = time.time()
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"Model loaded in {time.time() - start_time:.2f}s")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            self.model = None

    def index_colleges(self, colleges: List[Dict[str, Any]], aliases: Dict[str, str] = None):
        """Creates embeddings for a list of colleges, optionally enriched with aliases."""
        if not self.model or not colleges:
            return

        logger.info(f"Indexing {len(colleges)} colleges...")
        start_time = time.time()
        
        self.colleges_data = colleges
        self.college_names = []
        self.college_codes = []
        
        # Pre-process aliases: Map Full Name -> Space-separated Aliases
        # The input aliases is { "ALIAS": "FULL NAME" }
        alias_map = {}
        if aliases:
            for alias, full_name in aliases.items():
                upper_name = full_name.upper()
                if upper_name not in alias_map:
                    alias_map[upper_name] = []
                alias_map[upper_name].append(alias)
        
        # Prepare texts for embedding
        texts_to_embed = []
        
        for college in colleges:
            name = college.get('name', '')
            district = college.get('district', '')
            code = str(college.get('code', ''))
            
            # Check for aliases
            extra_context = ""
            if name.upper() in alias_map:
                extra_context = " " + " ".join(alias_map[name.upper()])
            
            # Composite string for better semantic matching
            # e.g. "Anna University Chennai 0001 CEG GUINDY"
            search_text = f"{name} {district} {code}{extra_context}"
            
            self.college_names.append(name)
            self.college_codes.append(code)
            texts_to_embed.append(search_text)

        try:
            self.college_embeddings = self.model.encode(texts_to_embed, convert_to_tensor=True)
            logger.info(f"Indexing completed in {time.time() - start_time:.2f}s")
        except Exception as e:
            logger.error(f"Failed to index colleges: {e}")
            self.college_embeddings = None

    def search(self, query: str, top_k: int = 5, threshold: float = 0.3) -> List[Tuple[Dict[str, Any], float]]:
        """
        Semantic search for colleges.
        Returns list of (college_dict, score) tuples.
        """
        if not self.model or self.college_embeddings is None:
            logger.warning("Search called but model/index not ready.")
            return []

        try:
            # Encode query
            query_embedding = self.model.encode(query, convert_to_tensor=True)
            
            # Compute cosine similarity
            cos_scores = util.cos_sim(query_embedding, self.college_embeddings)[0]
            
            # Get top k results
            top_results = torch.topk(cos_scores, k=min(top_k, len(self.colleges_data)))
            
            results = []
            for score, idx in zip(top_results.values, top_results.indices):
                score_val = float(score)
                if score_val >= threshold:
                    results.append((self.colleges_data[idx], score_val))
            
            return results
            
        except Exception as e:
            logger.error(f"Error during semantic search: {e}")
            return []

if __name__ == "__main__":
    # Simple test
    logging.basicConfig(level=logging.INFO)
    searcher = CollegeEmbeddingSearch()
    
    sample_colleges = [
        {"name": "College of Engineering Guindy", "district": "Chennai", "code": 1},
        {"name": "Madras Institute of Technology", "district": "Chennai", "code": 4},
        {"name": "SSN College of Engineering", "district": "Chengalpattu", "code": 1315},
    ]
    
    searcher.index_colleges(sample_colleges)
    
    TEST_QUERIES = [
        "CEG",
        "MIT chromeepet",
        "SSN",
        "Anna University main campus"
    ]
    
    for q in TEST_QUERIES:
        print(f"\nQuery: {q}")
        res = searcher.search(q, top_k=2)
        for c, s in res:
            print(f" - {c['name']} (Score: {s:.4f})")
