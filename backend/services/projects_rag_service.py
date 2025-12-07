"""
Projects RAG Service - Vector Store and Retrieval for Carbon Projects

This service:
1. Monitors projects.jsonl for changes
2. Generates embeddings using sentence-transformers
3. Stores embeddings in FAISS vector store
4. Provides RAG-based question answering on projects content
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
PROJECTS_JSONL_PATH = Path(__file__).parent.parent / "carbon-intelligence" / "server" / "output" / "projects.jsonl"
VECTOR_STORE_PATH = Path(__file__).parent.parent / "carbon-intelligence" / "server" / "output" / "projects_vector_store"
HASH_FILE_PATH = VECTOR_STORE_PATH / "projects_hash.txt"


class ProjectsRAGService:
    """
    RAG service for carbon credit projects.
    Maintains a FAISS vector store that syncs with projects.jsonl.
    """
    
    def __init__(self, projects_path: str = None, vector_store_path: str = None):
        """Initialize the RAG service."""
        self.projects_path = Path(projects_path) if projects_path else PROJECTS_JSONL_PATH
        self.vector_store_path = Path(vector_store_path) if vector_store_path else VECTOR_STORE_PATH
        self.hash_file_path = self.vector_store_path / "projects_hash.txt"
        
        self.vector_store: Optional[FAISS] = None
        self.embeddings = None
        self.text_splitter = None
        self._initialized = False
        self._lock = threading.Lock()
        self._watch_thread = None
        self._stop_watching = False
        
        # Store projects data for direct queries
        self._projects_data: List[Dict] = []
        
        if not LANGCHAIN_AVAILABLE:
            logger.error("❌ LangChain packages not available")
            return
        
        # Initialize embeddings model (using a small, fast model)
        logger.info("🚀 Loading embedding model for projects...")
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )
            logger.info("✅ Embedding model loaded for projects")
        except Exception as e:
            logger.error(f"❌ Failed to load embedding model: {e}")
            return
        
        # Text splitter for chunking project descriptions
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        # Initialize or load vector store
        self._initialize_vector_store()
    
    def _compute_file_hash(self) -> str:
        """Compute MD5 hash of projects.jsonl file."""
        if not self.projects_path.exists():
            return ""
        
        hash_md5 = hashlib.md5()
        with open(self.projects_path, "rb") as f:
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
    
    def _load_projects(self) -> List[Dict]:
        """Load projects from JSONL file."""
        projects = []
        if not self.projects_path.exists():
            logger.warning(f"⚠️ Projects file not found: {self.projects_path}")
            return projects
        
        with open(self.projects_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    project = json.loads(line.strip())
                    projects.append(project)
                except json.JSONDecodeError:
                    continue
        
        self._projects_data = projects
        logger.info(f"🌱 Loaded {len(projects)} carbon projects")
        return projects
    
    def _create_documents(self, projects: List[Dict]) -> List[Document]:
        """Convert projects to LangChain Documents with chunking."""
        documents = []
        
        total_projects = len(projects)
        for idx, project in enumerate(projects, start=1):
            # Print simple progress for document creation
            if idx % 100 == 0 or idx == total_projects:
                print(f"🔨 Creating document chunks: {idx}/{total_projects} projects processed", flush=True)
            project_id = project.get('project_id', '')
            project_name = project.get('project_name', '')
            description = project.get('description', '')
            methodology = project.get('methodology', '')
            status = project.get('registry_status', '')
            country = project.get('country', '')
            category = project.get('category', '')
            price = project.get('price', 'N/A')
            available_credits = project.get('available_credits', 'N/A')
            summary = project.get('project_summary', description)
            
            # Create content string
            content = f"""Project: {project_name}
Project ID: {project_id}
Country: {country}
Category: {category}
Methodology: {methodology}
Status: {status}
Price per Credit: ${price}
Available Credits: {available_credits:,} if isinstance(available_credits, int) else available_credits

Description: {description}

Summary: {summary}"""
            
            # Create metadata
            metadata = {
                'project_id': project_id,
                'project_name': project_name,
                'country': country,
                'category': category,
                'methodology': methodology,
                'status': status,
                'price': price,
                'available_credits': available_credits,
                'buy_link': project.get('buy_link', ''),
                'type': 'carbon_project'
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
        
        logger.info(f"📄 Created {len(documents)} project document chunks")
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
                logger.info("📂 Loading existing projects vector store...")
                self.vector_store = FAISS.load_local(
                    str(self.vector_store_path),
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                # Also load the projects data
                self._load_projects()
                self._initialized = True
                logger.info("✅ Projects vector store loaded successfully")
                return
            except Exception as e:
                logger.warning(f"⚠️ Failed to load projects vector store: {e}")
        
        # Build new vector store
        self._rebuild_vector_store()
    
    def _rebuild_vector_store(self):
        """Rebuild the entire vector store from projects.jsonl."""
        if not LANGCHAIN_AVAILABLE or self.embeddings is None:
            return
        
        with self._lock:
            logger.info("🔨 Building projects vector store...")
            
            projects = self._load_projects()
            if not projects:
                logger.warning("⚠️ No projects to index")
                return
            
            documents = self._create_documents(projects)
            if not documents:
                logger.warning("⚠️ No documents created")
                return
            
            try:
                # Manually embed documents in batches with progress reporting
                # (Can't monkey-patch HuggingFaceEmbeddings since it's a Pydantic model)
                print("🔁 Starting embedding with progress...", flush=True)
                
                texts = [doc.page_content for doc in documents]
                total = len(texts)
                batch_size = 512
                all_embeddings = []
                
                for i in range(0, total, batch_size):
                    batch = texts[i:i+batch_size]
                    batch_embeddings = self.embeddings.embed_documents(batch)
                    all_embeddings.extend(batch_embeddings)
                    done = i + len(batch)
                    pct = (done / total) * 100 if total else 100
                    print(f"\r🔁 Embedding progress: {done}/{total} ({pct:.1f}%)", end='', flush=True)
                
                print("")  # newline after progress
                
                # Build FAISS index from pre-computed embeddings
                print("🔨 Building FAISS index...", flush=True)
                text_embedding_pairs = list(zip(texts, all_embeddings))
                metadatas = [doc.metadata for doc in documents]
                self.vector_store = FAISS.from_embeddings(
                    text_embedding_pairs,
                    self.embeddings,
                    metadatas=metadatas
                )
                
                # Save to disk
                self.vector_store_path.mkdir(parents=True, exist_ok=True)
                self.vector_store.save_local(str(self.vector_store_path))
                
                # Save hash
                current_hash = self._compute_file_hash()
                self._save_hash(current_hash)
                
                self._initialized = True
                logger.info(f"✅ Projects vector store built with {len(documents)} chunks")
                
            except Exception as e:
                logger.error(f"❌ Failed to build projects vector store: {e}")
                import traceback
                traceback.print_exc()
    
    def check_and_update(self) -> bool:
        """Check if projects.jsonl has changed and update vector store if needed."""
        current_hash = self._compute_file_hash()
        stored_hash = self._get_stored_hash()
        
        if current_hash != stored_hash:
            logger.info("🔄 Projects file changed, rebuilding vector store...")
            self._rebuild_vector_store()
            return True
        return False
    
    def start_watching(self, interval: int = 60):
        """Start a background thread to watch for projects.jsonl changes."""
        if self._watch_thread is not None:
            return
        
        self._stop_watching = False
        
        def watch_loop():
            while not self._stop_watching:
                try:
                    self.check_and_update()
                except Exception as e:
                    logger.error(f"Error in projects watch loop: {e}")
                time.sleep(interval)
        
        self._watch_thread = threading.Thread(target=watch_loop, daemon=True)
        self._watch_thread.start()
        logger.info(f"👁️ Started watching projects.jsonl (interval: {interval}s)")
    
    def stop_watching(self):
        """Stop the background watch thread."""
        self._stop_watching = True
        if self._watch_thread:
            self._watch_thread.join(timeout=5)
            self._watch_thread = None
    
    def search(self, query: str, k: int = 5) -> List[Tuple[Document, float]]:
        """
        Search for relevant projects.
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of (Document, score) tuples
        """
        if not self._initialized or self.vector_store is None:
            logger.warning("⚠️ Projects vector store not initialized")
            return []
        
        try:
            results = self.vector_store.similarity_search_with_score(query, k=k)
            return results
        except Exception as e:
            logger.error(f"❌ Projects search error: {e}")
            return []
    
    def query(self, question: str, k: int = 5) -> Dict:
        """
        Query the projects corpus and return relevant context.
        
        Args:
            question: User's question
            k: Number of chunks to retrieve
            
        Returns:
            Dict with 'context', 'projects', and 'chunks'
        """
        results = self.search(question, k=k)
        
        if not results:
            return {
                'context': '',
                'projects': [],
                'chunks': [],
                'found': False
            }
        
        # Deduplicate projects
        seen_ids = set()
        projects = []
        chunks = []
        context_parts = []
        
        for doc, score in results:
            project_id = doc.metadata.get('project_id', '')
            
            # Add chunk info
            chunks.append({
                'content': doc.page_content,
                'score': float(score),
                'metadata': doc.metadata
            })
            
            # Add to context
            context_parts.append(doc.page_content)
            
            # Deduplicate projects
            if project_id and project_id not in seen_ids:
                seen_ids.add(project_id)
                projects.append({
                    'project_id': project_id,
                    'project_name': doc.metadata.get('project_name', ''),
                    'country': doc.metadata.get('country', ''),
                    'category': doc.metadata.get('category', ''),
                    'methodology': doc.metadata.get('methodology', ''),
                    'status': doc.metadata.get('status', ''),
                    'price': doc.metadata.get('price', 'N/A'),
                    'available_credits': doc.metadata.get('available_credits', 'N/A'),
                    'buy_link': doc.metadata.get('buy_link', '')
                })
        
        return {
            'context': '\n\n---\n\n'.join(context_parts),
            'projects': projects,
            'chunks': chunks,
            'found': True
        }
    
    def get_project_by_id(self, project_id: str) -> Optional[Dict]:
        """Get a specific project by ID."""
        for project in self._projects_data:
            if project.get('project_id', '').upper() == project_id.upper():
                return project
        return None
    
    def get_projects_by_country(self, country: str) -> List[Dict]:
        """Get projects by country."""
        country_lower = country.lower()
        return [p for p in self._projects_data if country_lower in p.get('country', '').lower()]
    
    def get_projects_by_category(self, category: str) -> List[Dict]:
        """Get projects by category."""
        category_lower = category.lower()
        return [p for p in self._projects_data if category_lower in p.get('category', '').lower()]
    
    def list_all_countries(self) -> List[str]:
        """List all unique countries with projects."""
        countries = set()
        for project in self._projects_data:
            country = project.get('country', '')
            if country:
                countries.add(country)
        return sorted(list(countries))
    
    def list_all_categories(self) -> List[str]:
        """List all unique project categories."""
        categories = set()
        for project in self._projects_data:
            category = project.get('category', '')
            if category:
                categories.add(category)
        return sorted(list(categories))
    
    def get_stats(self) -> Dict:
        """Get statistics about the vector store."""
        stats = {
            'initialized': self._initialized,
            'projects_file_exists': self.projects_path.exists(),
            'vector_store_exists': (self.vector_store_path / "index.faiss").exists(),
        }
        
        if self._projects_data:
            stats['total_projects'] = len(self._projects_data)
            stats['countries'] = len(self.list_all_countries())
            stats['categories'] = len(self.list_all_categories())
        
        if self.vector_store:
            stats['total_chunks'] = self.vector_store.index.ntotal
        
        return stats


# Global instance
_projects_rag_service: Optional[ProjectsRAGService] = None


def get_projects_rag_service() -> Optional[ProjectsRAGService]:
    """Get or create the global ProjectsRAGService instance."""
    global _projects_rag_service
    
    if _projects_rag_service is None:
        _projects_rag_service = ProjectsRAGService()
        _projects_rag_service.start_watching(interval=60)  # Check every minute
    
    return _projects_rag_service


def search_projects(query: str, k: int = 5) -> Dict:
    """
    Search carbon projects using RAG.
    
    Args:
        query: Search query or question
        k: Number of results
        
    Returns:
        Dict with context, projects, and chunks
    """
    service = get_projects_rag_service()
    if service:
        return service.query(query, k=k)
    return {'context': '', 'projects': [], 'chunks': [], 'found': False}


# For testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("🚀 Testing Projects RAG Service...")
    service = ProjectsRAGService()
    
    print("\n📊 Stats:", service.get_stats())
    
    # Test search
    test_queries = [
        "forestry projects in India",
        "renewable energy carbon credits",
        "cheapest carbon credits"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Query: {query}")
        results = service.query(query, k=3)
        print(f"   Found: {results['found']}")
        print(f"   Projects: {len(results['projects'])}")
        for proj in results['projects'][:2]:
            print(f"   - {proj['project_name'][:50]}... ({proj['country']})")
