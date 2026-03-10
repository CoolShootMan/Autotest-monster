import os
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from loguru import logger

class RAGKnowledgeBase:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(RAGKnowledgeBase, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, 'initialized'): return
        
        self.kb_path = os.path.join(os.path.dirname(__file__), "Knowledge_Base.md")
        self.chunks = []
        self.index = None
        self.model = None
        
        self._load_and_index()
        self.initialized = True

    def _load_and_index(self):
        try:
            logger.info("Initializing RAG Knowledge Base... Loading model (this might take a moment).")
            # Use a fast, small model
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            
            if not os.path.exists(self.kb_path):
                logger.warning(f"Knowledge Base file not found at {self.kb_path}")
                return
                
            with open(self.kb_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            # Naive chunking by lists and headings
            raw_chunks = content.split("* **")
            raw_chunks += content.split("### ")
            
            # Clean and filter chunks
            self.chunks = []
            for chunk in raw_chunks:
                clean_chunk = chunk.strip()
                if clean_chunk and len(clean_chunk) > 20: 
                    self.chunks.append(clean_chunk)
                    
            if not self.chunks:
                logger.warning("No valid chunks extracted from Knowledge Base.")
                return
                
            logger.info(f"Encoding {len(self.chunks)} knowledge chunks...")
            embeddings = self.model.encode(self.chunks)
            
            # Create Faiss index
            dim = embeddings.shape[1]
            self.index = faiss.IndexFlatL2(dim)
            self.index.add(np.array(embeddings).astype('float32'))
            logger.info("RAG Knowledge Base indexing complete.")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG Knowledge Base: {e}")
            self.chunks = []

    def query(self, query_text: str, top_k: int = 2) -> str:
        """Query the knowledge base and return relevant text."""
        if not self.index or not self.chunks:
            return ""
            
        try:
            query_vector = self.model.encode([query_text])
            D, I = self.index.search(np.array(query_vector).astype('float32'), top_k)
            
            results = []
            for idx in I[0]:
                if idx != -1 and idx < len(self.chunks):
                    # Re-add prefix for context
                    results.append(f"- {self.chunks[idx][:300]}...") # truncate for prompt
            
            if results:
                return "Retrieved Knowledge Context:\n" + "\n".join(results)
            return ""
        except Exception as e:
            logger.error(f"RAG query failed: {e}")
            return ""

# Global instance
rag_kb = RAGKnowledgeBase()
