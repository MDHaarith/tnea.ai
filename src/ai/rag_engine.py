
import os
import chromadb
from chromadb.utils import embedding_functions
import logging
from typing import List, Dict, Any

logger = logging.getLogger("tnea_ai.rag")

class GuidelineRAG:
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            # Resolves to tnea.ai/data assuming this file is in src/ai/
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.data_dir = os.path.join(base_dir, "data")
        else:
            self.data_dir = data_dir
            
        self.vector_store_path = os.path.join(self.data_dir, "vector_store")
        
        # Initialize ChromaDB
        try:
            self.client = chromadb.PersistentClient(path=self.vector_store_path)
            
            # Use same model as embedding search for consistency
            self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
            
            self.collection = self.client.get_or_create_collection(
                name="tnea_guidelines",
                embedding_function=self.embedding_fn
            )
            
            # Check if empty, then ingest
            if self.collection.count() == 0:
                self.ingest_guidelines()
                
        except Exception as e:
            logger.error(f"Failed to initialize RAG Engine: {e}")
            self.client = None
            self.collection = None

    def ingest_guidelines(self):
        """Read text file, chunk it, and store in vector DB."""
        file_path = os.path.join(self.data_dir, "docs", "tnea_guidelines.txt")
        if not os.path.exists(file_path):
            logger.error(f"Guideline file not found at {file_path}")
            return
            
        logger.info("Ingesting guidelines...")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
                
            # Simple chunking: 1000 chars with overlap
            chunk_size = 1000
            overlap = 200
            chunks = []
            ids = []
            metadatas = []
            
            for i in range(0, len(text), chunk_size - overlap):
                chunk = text[i:i + chunk_size]
                if len(chunk) < 100:
                    continue
                chunks.append(chunk)
                ids.append(f"chunk_{i}")
                metadatas.append({"source": "tnea_guidelines"})
                
            self.collection.add(
                documents=chunks,
                ids=ids,
                metadatas=metadatas
            )
            logger.info(f"Ingested {len(chunks)} chunks into ChromaDB.")
            
        except Exception as e:
            logger.error(f"Error during ingestion: {e}")

    def query(self, query_text: str, n_results: int = 3) -> str:
        """Retrieve relevant context for a query."""
        if not self.collection:
            return ""
            
        try:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results
            )
            
            # results['documents'] is a list of lists (one list per query)
            documents = results.get('documents', [[]])[0]
            
            if not documents:
                return ""
                
            return "\n\n---\n\n".join(documents)
            
        except Exception as e:
            logger.error(f"RAG Retrieval failed: {e}")
            return ""

if __name__ == "__main__":
    # Test run
    rag = GuidelineRAG()
    print("Collection count:", rag.collection.count())
    res = rag.query("What is the fee for SC students?")
    print("Query Result:\n", res[:200], "...")
