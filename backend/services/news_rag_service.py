"""
News RAG Service - Vector Store and Retrieval Augmented Generation

This service:
1. Monitors news.jsonl for changes
2. Generates embeddings using sentence-transformers
3. Stores embeddings in FAISS vector store
4. Provides RAG-based question answering on news content
"""

import os
import json
import logging
import hashlib
import threading
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime

# Vector store and embeddings
LANGCHAIN_AVAILABLE = False
FAISS = None
HuggingFaceEmbeddings = None
RecursiveCharacterTextSplitter = None
Document = None

try:
    # Try langchain-community first
    from langchain_community.vectorstores import FAISS as _FAISS
    from langchain_community.embeddings import HuggingFaceEmbeddings as _HuggingFaceEmbeddings
    FAISS = _FAISS
    HuggingFaceEmbeddings = _HuggingFaceEmbeddings
except ImportError:
    pass

try:
    # Try langchain_core for Document
    from langchain_core.documents import Document as _Document
    Document = _Document
except ImportError:
    try:
        from langchain.schema import Document as _Document
        Document = _Document
    except ImportError:
        pass

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter as _RecursiveCharacterTextSplitter
    RecursiveCharacterTextSplitter = _RecursiveCharacterTextSplitter
except ImportError:
    try:
        from langchain.text_splitter import RecursiveCharacterTextSplitter as _RecursiveCharacterTextSplitter
        RecursiveCharacterTextSplitter = _RecursiveCharacterTextSplitter
    except ImportError:
        pass

# Check if all required components are available
if FAISS is not None and HuggingFaceEmbeddings is not None and Document is not None and RecursiveCharacterTextSplitter is not None:
    LANGCHAIN_AVAILABLE = True
else:
    print("⚠️ LangChain community packages not available. Install with: pip install langchain-community faiss-cpu sentence-transformers")

logger = logging.getLogger(__name__)

# Paths
NEWS_JSONL_PATH = Path(__file__).parent.parent / "carbon-intelligence" / "server" / "output" / "news.jsonl"
VECTOR_STORE_PATH = Path(__file__).parent.parent / "carbon-intelligence" / "server" / "output" / "news_vector_store"
HASH_FILE_PATH = VECTOR_STORE_PATH / "news_hash.txt"


class NewsRAGService:
    """
    RAG service for carbon/ESG news articles.
    Maintains a FAISS vector store that syncs with news.jsonl.
    """
    
    def __init__(self, news_path: str = None, vector_store_path: str = None):
        """Initialize the RAG service."""
        self.news_path = Path(news_path) if news_path else NEWS_JSONL_PATH
        self.vector_store_path = Path(vector_store_path) if vector_store_path else VECTOR_STORE_PATH
        self.hash_file_path = self.vector_store_path / "news_hash.txt"
        
        self.vector_store: Optional[FAISS] = None
        self.embeddings = None
        self.text_splitter = None
        self._initialized = False
        self._lock = threading.Lock()
        self._watch_thread = None
        self._stop_watching = False
        
        if not LANGCHAIN_AVAILABLE:
            logger.error("❌ LangChain packages not available")
            return
        
        # Initialize embeddings model (using a small, fast model)
        logger.info("🚀 Loading embedding model...")
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )
            logger.info("✅ Embedding model loaded")
        except Exception as e:
            logger.error(f"❌ Failed to load embedding model: {e}")
            return
        
        # Text splitter for chunking articles
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        # Initialize or load vector store
        self._initialize_vector_store()
    
    def _compute_file_hash(self) -> str:
        """Compute MD5 hash of news.jsonl file."""
        if not self.news_path.exists():
            return ""
        
        hash_md5 = hashlib.md5()
        with open(self.news_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _get_stored_hash(self) -> str:
        """Get the stored hash from previous indexing."""
        if self.hash_file_path.exists():
            return self.hash_file_path.read_text().strip()
        return ""
    
    def _save_hash(self, hash_value: str):
        """Save the current hash."""
        self.vector_store_path.mkdir(parents=True, exist_ok=True)
        self.hash_file_path.write_text(hash_value)
    
    def _load_news_articles(self) -> List[Dict]:
        """Load news articles from JSONL file."""
        articles = []
        if not self.news_path.exists():
            logger.warning(f"⚠️ News file not found: {self.news_path}")
            return articles
        
        with open(self.news_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    article = json.loads(line.strip())
                    articles.append(article)
                except json.JSONDecodeError:
                    continue
        
        logger.info(f"📰 Loaded {len(articles)} news articles")
        return articles
    
    def _create_documents(self, articles: List[Dict]) -> List[Document]:
        """Convert articles to LangChain Documents with chunking."""
        documents = []
        
        for article in articles:
            # Extract clean text content
            title = article.get('title', '').strip()
            # Clean HTML from summary
            summary = article.get('summary', '')
            # Remove HTML tags
            import re
            summary = re.sub(r'<[^>]+>', '', summary).strip()
            
            source = article.get('source', 'Unknown')
            published = article.get('published', '')
            sentiment = article.get('sentiment', 'Neutral')
            link = article.get('link', '')
            
            # Create content string
            content = f"Title: {title}\n\nSource: {source}\nPublished: {published}\nSentiment: {sentiment}\n\n{summary}"
            
            # Create metadata
            metadata = {
                'title': title,
                'source': source,
                'published': published,
                'sentiment': sentiment,
                'link': link,
                'type': 'news_article'
            }
            
            # Split into chunks if content is long
            if len(content) > 500:
                chunks = self.text_splitter.split_text(content)
                for i, chunk in enumerate(chunks):
                    chunk_metadata = metadata.copy()
                    chunk_metadata['chunk_index'] = i
                    documents.append(Document(page_content=chunk, metadata=chunk_metadata))
            else:
                documents.append(Document(page_content=content, metadata=metadata))
        
        logger.info(f"📄 Created {len(documents)} document chunks")
        return documents
    
    def _initialize_vector_store(self):
        """Initialize or load the vector store."""
        if not LANGCHAIN_AVAILABLE or self.embeddings is None:
            return
        
        current_hash = self._compute_file_hash()
        stored_hash = self._get_stored_hash()
        
        # Check if we can load existing vector store
        faiss_index_path = self.vector_store_path / "index.faiss"
        if faiss_index_path.exists() and current_hash == stored_hash:
            try:
                logger.info("📂 Loading existing vector store...")
                self.vector_store = FAISS.load_local(
                    str(self.vector_store_path),
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                self._initialized = True
                logger.info("✅ Vector store loaded successfully")
                return
            except Exception as e:
                logger.warning(f"⚠️ Failed to load vector store: {e}")
        
        # Build new vector store
        self._rebuild_vector_store()
    
    def _rebuild_vector_store(self):
        """Rebuild the entire vector store from news.jsonl."""
        if not LANGCHAIN_AVAILABLE or self.embeddings is None:
            return
        
        with self._lock:
            logger.info("🔨 Building vector store from news.jsonl...")
            
            articles = self._load_news_articles()
            if not articles:
                logger.warning("⚠️ No articles to index")
                return
            
            documents = self._create_documents(articles)
            if not documents:
                logger.warning("⚠️ No documents created")
                return
            
            try:
                # Create FAISS vector store
                self.vector_store = FAISS.from_documents(
                    documents,
                    self.embeddings
                )
                
                # Save to disk
                self.vector_store_path.mkdir(parents=True, exist_ok=True)
                self.vector_store.save_local(str(self.vector_store_path))
                
                # Save hash
                current_hash = self._compute_file_hash()
                self._save_hash(current_hash)
                
                self._initialized = True
                logger.info(f"✅ Vector store built with {len(documents)} chunks")
                
            except Exception as e:
                logger.error(f"❌ Failed to build vector store: {e}")
                import traceback
                traceback.print_exc()
    
    def check_and_update(self) -> bool:
        """Check if news.jsonl has changed and update vector store if needed."""
        current_hash = self._compute_file_hash()
        stored_hash = self._get_stored_hash()
        
        if current_hash != stored_hash:
            logger.info("🔄 News file changed, rebuilding vector store...")
            self._rebuild_vector_store()
            return True
        return False
    
    def start_watching(self, interval: int = 60):
        """Start a background thread to watch for news.jsonl changes."""
        if self._watch_thread is not None:
            return
        
        self._stop_watching = False
        
        def watch_loop():
            while not self._stop_watching:
                try:
                    self.check_and_update()
                except Exception as e:
                    logger.error(f"Error in watch loop: {e}")
                time.sleep(interval)
        
        self._watch_thread = threading.Thread(target=watch_loop, daemon=True)
        self._watch_thread.start()
        logger.info(f"👁️ Started watching news.jsonl (interval: {interval}s)")
    
    def stop_watching(self):
        """Stop the background watch thread."""
        self._stop_watching = True
        if self._watch_thread:
            self._watch_thread.join(timeout=5)
            self._watch_thread = None
    
    def search(self, query: str, k: int = 5) -> List[Tuple[Document, float]]:
        """
        Search for relevant news articles.
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of (Document, score) tuples
        """
        if not self._initialized or self.vector_store is None:
            logger.warning("⚠️ Vector store not initialized")
            return []
        
        try:
            results = self.vector_store.similarity_search_with_score(query, k=k)
            return results
        except Exception as e:
            logger.error(f"❌ Search error: {e}")
            return []
    
    def query(self, question: str, k: int = 5) -> Dict:
        """
        Query the news corpus and return relevant context.
        
        Args:
            question: User's question
            k: Number of chunks to retrieve
            
        Returns:
            Dict with 'context', 'sources', and 'chunks'
        """
        results = self.search(question, k=k)
        
        if not results:
            return {
                'context': '',
                'sources': [],
                'chunks': [],
                'found': False
            }
        
        # Deduplicate sources
        seen_titles = set()
        sources = []
        chunks = []
        context_parts = []
        
        for doc, score in results:
            title = doc.metadata.get('title', '')
            
            # Add chunk info
            chunks.append({
                'content': doc.page_content,
                'score': float(score),
                'metadata': doc.metadata
            })
            
            # Add to context
            context_parts.append(doc.page_content)
            
            # Deduplicate sources
            if title and title not in seen_titles:
                seen_titles.add(title)
                sources.append({
                    'title': title,
                    'source': doc.metadata.get('source', 'Unknown'),
                    'published': doc.metadata.get('published', ''),
                    'sentiment': doc.metadata.get('sentiment', 'Neutral'),
                    'link': doc.metadata.get('link', '')
                })
        
        return {
            'context': '\n\n---\n\n'.join(context_parts),
            'sources': sources,
            'chunks': chunks,
            'found': True
        }
    
    def get_stats(self) -> Dict:
        """Get statistics about the vector store."""
        stats = {
            'initialized': self._initialized,
            'news_file_exists': self.news_path.exists(),
            'vector_store_exists': (self.vector_store_path / "index.faiss").exists(),
        }
        
        if self.news_path.exists():
            articles = self._load_news_articles()
            stats['total_articles'] = len(articles)
        
        if self.vector_store:
            stats['total_chunks'] = self.vector_store.index.ntotal
        
        return stats


# Global instance
_news_rag_service: Optional[NewsRAGService] = None


def get_news_rag_service() -> Optional[NewsRAGService]:
    """Get or create the global NewsRAGService instance."""
    global _news_rag_service
    
    if _news_rag_service is None:
        _news_rag_service = NewsRAGService()
        _news_rag_service.start_watching(interval=60)  # Check every minute
    
    return _news_rag_service


def search_news(query: str, k: int = 5) -> Dict:
    """
    Search news articles using RAG.
    
    Args:
        query: Search query or question
        k: Number of results
        
    Returns:
        Dict with context, sources, and chunks
    """
    service = get_news_rag_service()
    if service:
        return service.query(query, k=k)
    return {'context': '', 'sources': [], 'chunks': [], 'found': False}


# For testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("🚀 Testing News RAG Service...")
    service = NewsRAGService()
    
    print("\n📊 Stats:", service.get_stats())
    
    # Test search
    test_queries = [
        "carbon credits",
        "ESG investing trends",
        "sustainable energy news"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Query: {query}")
        results = service.query(query, k=3)
        print(f"   Found: {results['found']}")
        print(f"   Sources: {len(results['sources'])}")
        for src in results['sources'][:2]:
            print(f"   - {src['title'][:60]}...")
