import os
import asyncio
from typing import Optional, Any, Dict
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext, load_index_from_storage, Settings
from llama_index.llms.openai import OpenAI as LlamaOpenAI
from llama_index.embeddings.openai import OpenAIEmbedding as LlamaOpenAIEmbedding
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.postprocessor import SimilarityPostprocessor
from src.core.config import Config
from src.core.logger import logger

class KnowledgeBaseService:
    """Service for managing knowledge base using LlamaIndex with enhanced error handling"""
    
    def __init__(self):
        self.query_engine = None
        self.index = None
        self._initialized = False
        self._initialization_lock = asyncio.Lock() if hasattr(asyncio, 'Lock') else None
        self._max_retries = 3
        # In-memory cache for recent queries
        self._query_cache: dict[str, str] = {}
        self._cache_max_size: int = 128
    
    async def initialize(self) -> bool:
        """
        Initialize the knowledge base with async support and retry logic
        
        Returns:
            Success status
        """
        if self._initialized:
            return True
            
        # Use lock to prevent concurrent initialization
        if self._initialization_lock:
            async with self._initialization_lock:
                if self._initialized:  # Double check after acquiring lock
                    return True
                return await self._do_initialize()
        else:
            return await self._do_initialize()
    
    async def _do_initialize(self) -> bool:
        """Internal initialization method"""
        if not Config.OPENAI_API_KEY:
            logger.error("Cannot initialize knowledge base - OPENAI_API_KEY missing")
            return False
        
        for attempt in range(self._max_retries):
            try:
                logger.info(f"Initializing LlamaIndex knowledge base (attempt {attempt + 1}/{self._max_retries})...")
                
                # Configure global settings
                Settings.llm = LlamaOpenAI(
                    model=Config.OPENAI_MODEL,
                    api_key=Config.OPENAI_API_KEY,
                    temperature=0.1,
                    max_tokens=512
                )
                
                Settings.embed_model = LlamaOpenAIEmbedding(
                    api_key=Config.OPENAI_API_KEY,
                    model="text-embedding-3-small"
                )
                
                # Load or create index
                if await self._storage_exists():
                    logger.info("Loading existing vector store...")
                    storage_context = StorageContext.from_defaults(
                        persist_dir=str(Config.VECTOR_STORE_DIR)
                    )
                    self.index = load_index_from_storage(storage_context)
                else:
                    logger.info("Creating new vector store...")
                    documents = await self._load_documents()
                    
                    if documents:
                        self.index = VectorStoreIndex.from_documents(documents)
                    else:
                        # Create empty index if no documents
                        self.index = VectorStoreIndex([])
                    
                    # Persist the index
                    self.index.storage_context.persist(persist_dir=str(Config.VECTOR_STORE_DIR))
                
                # Create advanced query engine with post-processing
                retriever = VectorIndexRetriever(
                    index=self.index,
                    similarity_top_k=Config.SIMILARITY_TOP_K
                )
                
                # Add similarity post-processor to filter low-quality results
                postprocessor = SimilarityPostprocessor(similarity_cutoff=0.7)
                
                self.query_engine = RetrieverQueryEngine(
                    retriever=retriever,
                    node_postprocessors=[postprocessor]
                )
                
                self._initialized = True
                logger.info("Knowledge base initialized successfully")
                return True
                
            except Exception as e:
                logger.error(f"Failed to initialize knowledge base (attempt {attempt + 1}): {e}")
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                continue
                
        logger.error("Failed to initialize knowledge base after all retries")
        return False
    
    async def query(self, question: str, context: Optional[str] = None) -> Optional[str]:
        """
        Query the knowledge base with enhanced context and error handling
        
        Args:
            question: User question
            context: Optional conversation context
            
        Returns:
            Answer from knowledge base or None
        """
        key = (question.strip(), context or "")
        # Return cached answer if available
        cached = self._query_cache.get(key)
        if cached:
            logger.debug(f"Cache hit for query: {question[:50]}...")
            return cached
        
        if not question or not question.strip():
            logger.warning("Empty question provided to knowledge base")
            return None
            
        if not self._initialized:
            if not await self.initialize():
                return None
        
        try:
            # Enhance query with context if provided
            enhanced_query = question
            if context:
                enhanced_query = f"Context: {context}\n\nQuestion: {question}"
            
            logger.debug(f"Querying knowledge base: {enhanced_query[:100]}...")
            
            # Add timeout to prevent hanging
            response = await asyncio.wait_for(
                self._execute_query(enhanced_query),
                timeout=30.0
            )
            
            if response and str(response).strip():
                answer = str(response).strip()
                logger.debug(f"Knowledge base response: {answer[:100]}...")
                
                # Post-process response
                answer = self._post_process_response(answer)
                # Cache the answer
                if answer:
                    if len(self._query_cache) >= self._cache_max_size:
                        # evict oldest entry
                        self._query_cache.pop(next(iter(self._query_cache)))
                    self._query_cache[key] = answer
                return answer if answer else None
            else:
                logger.debug("Knowledge base returned empty response")
                return None
                
        except asyncio.TimeoutError:
            logger.error("Knowledge base query timed out")
            return None
        except Exception as e:
            logger.error(f"Knowledge base query error: {e}")
            return None
    
    async def _execute_query(self, query: str):
        """Execute the actual query"""
        # Run the synchronous query in a thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.query_engine.query, query)
    
    def _post_process_response(self, response: str) -> str:
        """Post-process the response to improve quality"""
        # Remove common artifacts
        response = response.replace("Based on the provided context,", "")
        response = response.replace("According to the information provided,", "")
        response = response.strip()
        
        # Ensure response is not too short or too long
        if len(response) < 10:
            return ""
        
        if len(response) > 1000:
            # Truncate at last complete sentence
            sentences = response.split('.')
            truncated = ""
            for sentence in sentences:
                if len(truncated + sentence + ".") <= 1000:
                    truncated += sentence + "."
                else:
                    break
            response = truncated if truncated else response[:1000] + "..."
        
        return response
    
    async def _storage_exists(self) -> bool:
        """Check if vector store exists asynchronously"""
        try:
            docstore_path = Config.VECTOR_STORE_DIR / "docstore.json"
            return docstore_path.exists() and docstore_path.stat().st_size > 0
        except Exception as e:
            logger.error(f"Error checking storage existence: {e}")
            return False
    
    async def _load_documents(self) -> list:
        """Load documents from data directory asynchronously"""
        try:
            if not Config.LLAMA_DATA_DIR.exists():
                logger.warning(f"Data directory not found: {Config.LLAMA_DATA_DIR}")
                return []
            
            # Run document loading in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            documents = await loop.run_in_executor(
                None, 
                self._load_documents_sync
            )
            
            logger.info(f"Loaded {len(documents)} documents")
            return documents
            
        except Exception as e:
            logger.error(f"Error loading documents: {e}")
            return []
    
    def _load_documents_sync(self) -> list:
        """Synchronous document loading"""
        reader = SimpleDirectoryReader(
            input_dir=str(Config.LLAMA_DATA_DIR),
            recursive=True,
            filename_as_id=True
        )
        return reader.load_data()
    
    async def rebuild_index(self) -> bool:
        """
        Rebuild the vector store index asynchronously
        
        Returns:
            Success status
        """
        try:
            logger.info("Rebuilding knowledge base index...")
            
            # Remove existing storage
            if Config.VECTOR_STORE_DIR.exists():
                import shutil
                shutil.rmtree(Config.VECTOR_STORE_DIR)
            
            Config.VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)
            
            # Reset initialization flag
            self._initialized = False
            self.query_engine = None
            self.index = None
            
            # Reinitialize
            return await self.initialize()
            
        except Exception as e:
            logger.error(f"Error rebuilding index: {e}")
            return False
    
    async def add_document(self, document_path: str) -> bool:
        """
        Add a new document to the knowledge base
        
        Args:
            document_path: Path to the document to add
            
        Returns:
            Success status
        """
        try:
            if not self._initialized:
                if not await self.initialize():
                    return False
            
            # Load the new document
            reader = SimpleDirectoryReader(input_files=[document_path])
            documents = reader.load_data()
            
            if not documents:
                logger.warning(f"No documents loaded from {document_path}")
                return False
            
            # Add to existing index
            for doc in documents:
                self.index.insert(doc)
            
            # Persist changes
            self.index.storage_context.persist(persist_dir=str(Config.VECTOR_STORE_DIR))
            
            logger.info(f"Successfully added document: {document_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding document {document_path}: {e}")
            return False
    
    async def query_async(self, question: str, context: str = "", timeout: float = 30.0) -> Optional[str]:
        """
        Async version of query method
        
        Args:
            question: The question to ask
            context: Additional context for the query
            timeout: Query timeout in seconds
            
        Returns:
            Answer or None if no answer found
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.query, question, context, timeout)
    
    async def rebuild_index_async(self) -> bool:
        """
        Async version of rebuild_index method
        
        Returns:
            Success status
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.rebuild_index)
    
    async def add_document_async(self, document_text: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Async version of add_document method
        
        Args:
            document_text: Text content to add
            metadata: Optional metadata for the document
            
        Returns:
            Success status
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.add_document, document_text, metadata)
    
    def get_stats(self) -> dict:
        """Get knowledge base statistics"""
        try:
            if not self._initialized or not self.index:
                return {"status": "not_initialized"}
            
            # Get basic stats
            doc_count = len(self.index.docstore.docs)
            
            return {
                "status": "initialized",
                "document_count": doc_count,
                "storage_dir": str(Config.VECTOR_STORE_DIR),
                "data_dir": str(Config.LLAMA_DATA_DIR)
            }
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {"status": "error", "error": str(e)}

# Global knowledge base service instance
knowledge_base = KnowledgeBaseService()
