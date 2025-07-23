"""
Optimized ChromaDB vector store with batch processing and caching
Performance improvements for large document processing
"""
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import json
import logging
import asyncio
import numpy as np
from typing import List, Dict, Optional, Tuple
import uuid
from concurrent.futures import ThreadPoolExecutor
import hashlib

from backend.core.config import get_settings
from backend.core.performance_optimizer import performance_optimizer, timed

logger = logging.getLogger(__name__)

class OptimizedVectorStore:
    """High-performance ChromaDB vector store with optimizations"""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = None
        self.collection = None
        self.embedding_model = None
        self.executor = ThreadPoolExecutor(max_workers=4)
        self._embedding_cache = {}
        self._initialize()
    
    def _initialize(self):
        """Initialize ChromaDB client and collection with optimizations"""
        try:
            # Create ChromaDB client with optimized settings
            self.client = chromadb.PersistentClient(
                path=self.settings.chroma_persist_dir,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Load embedding model with optimizations
            logger.info("Loading optimized BAAI/bge-base-en-v1.5 embedding model...")
            self.embedding_model = SentenceTransformer(
                'BAAI/bge-base-en-v1.5',
                device='cpu'  # Explicit CPU usage for consistency
            )
            
            # Enable model optimizations
            self.embedding_model.eval()  # Set to evaluation mode for inference
            logger.info("✅ Optimized embedding model loaded")
            
            # Get or create collection with optimized metadata
            try:
                self.collection = self.client.get_collection("ragdemo_documents")
                logger.info("✅ Connected to existing ChromaDB collection")
            except ValueError:
                # Collection doesn't exist, create with optimizations
                self.collection = self.client.create_collection(
                    name="ragdemo_documents",
                    metadata={
                        "hnsw:space": "cosine",
                        "hnsw:construction_ef": 200,  # Higher for better quality
                        "hnsw:M": 16,  # Optimal connections per node
                        "hnsw:ef_search": 100,  # Search parameter
                    }
                )
                logger.info("✅ Created optimized ChromaDB collection")
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize optimized vector store: {e}")
            raise RuntimeError(f"Vector store initialization failed: {e}")
    
    def _get_embedding_cache_key(self, text: str) -> str:
        """Generate cache key for embeddings"""
        return hashlib.md5(text.encode()).hexdigest()
    
    def _cache_embedding(self, text: str, embedding: np.ndarray):
        """Cache embedding for reuse"""
        cache_key = self._get_embedding_cache_key(text)
        self._embedding_cache[cache_key] = embedding.tolist()
        
        # Limit cache size
        if len(self._embedding_cache) > 1000:
            # Remove oldest entries (simple LRU)
            keys_to_remove = list(self._embedding_cache.keys())[:100]
            for key in keys_to_remove:
                del self._embedding_cache[key]
    
    def _get_cached_embedding(self, text: str) -> Optional[List[float]]:
        """Get cached embedding if available"""
        cache_key = self._get_embedding_cache_key(text)
        return self._embedding_cache.get(cache_key)
    
    def _generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings in batch for better performance"""
        # Check cache first
        embeddings = []
        texts_to_process = []
        cache_indices = []
        
        for i, text in enumerate(texts):
            cached = self._get_cached_embedding(text)
            if cached:
                embeddings.append(cached)
                cache_indices.append(i)
            else:
                texts_to_process.append(text)
                embeddings.append(None)  # Placeholder
        
        # Process uncached texts in batch
        if texts_to_process:
            logger.info(f"Generating {len(texts_to_process)} new embeddings (cached: {len(cache_indices)})")
            
            # Batch encode for efficiency
            new_embeddings = self.embedding_model.encode(
                texts_to_process,
                batch_size=32,  # Optimal batch size for CPU
                show_progress_bar=len(texts_to_process) > 10,
                convert_to_tensor=False
            )
            
            # Cache new embeddings and fill placeholders
            j = 0
            for i, embedding in enumerate(embeddings):
                if embedding is None:  # Was a placeholder
                    embeddings[i] = new_embeddings[j].tolist()
                    self._cache_embedding(texts[i], new_embeddings[j])
                    j += 1
        
        return embeddings
    
    @timed("add_document_chunks")
    def add_document_chunks(self, chunks: List[Dict]) -> int:
        """
        Add document chunks with batch processing optimization
        
        Args:
            chunks: List of chunk dictionaries
            
        Returns:
            Number of chunks added
        """
        if not chunks:
            return 0
        
        try:
            logger.info(f"Processing {len(chunks)} chunks with batch optimization...")
            
            # Prepare data for ChromaDB
            ids = []
            texts = []
            metadatas = []
            
            for chunk in chunks:
                chunk_id = chunk.get('id', str(uuid.uuid4()))
                text = chunk['text']
                
                ids.append(chunk_id)
                texts.append(text)
                metadatas.append({
                    "document": chunk.get('document', 'unknown'),
                    "page": chunk.get('page', 0),
                    "images": json.dumps(chunk.get('images', [])),
                    "word_count": chunk.get('word_count', len(text.split()))
                })
            
            # Generate embeddings in batch
            embeddings = self._generate_embeddings_batch(texts)
            
            # Add to collection in batches for memory efficiency
            batch_size = 100
            total_added = 0
            
            for i in range(0, len(chunks), batch_size):
                end_idx = min(i + batch_size, len(chunks))
                batch_ids = ids[i:end_idx]
                batch_texts = texts[i:end_idx]
                batch_embeddings = embeddings[i:end_idx]
                batch_metadatas = metadatas[i:end_idx]
                
                self.collection.add(
                    ids=batch_ids,
                    documents=batch_texts,
                    embeddings=batch_embeddings,
                    metadatas=batch_metadatas
                )
                
                total_added += len(batch_ids)
                logger.debug(f"Added batch {i//batch_size + 1}: {len(batch_ids)} chunks")
            
            logger.info(f"✅ Added {total_added} chunks to optimized vector store")
            return total_added
            
        except Exception as e:
            logger.error(f"❌ Failed to add chunks to vector store: {e}")
            raise RuntimeError(f"Failed to add document chunks: {e}")
    
    @timed("vector_search")
    async def search(self, query: str, limit: int = 5) -> List[Dict]:
        """
        Optimized semantic search with caching and performance improvements
        
        Args:
            query: Search query string
            limit: Maximum number of results to return
            
        Returns:
            List of relevant chunk dictionaries
        """
        try:
            # Check cache first
            cache_key = f"search:{hashlib.md5(f'{query}:{limit}'.encode()).hexdigest()}"
            cached_result = performance_optimizer.get_cached_result(cache_key)
            if cached_result:
                logger.debug(f"Cache hit for query: {query[:50]}...")
                return cached_result
            
            # Generate query embedding
            loop = asyncio.get_event_loop()
            query_embedding = await loop.run_in_executor(
                self.executor,
                lambda: self.embedding_model.encode(query).tolist()
            )
            
            # Search in ChromaDB with optimized parameters
            results = await loop.run_in_executor(
                self.executor,
                lambda: self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=limit,
                    include=['documents', 'metadatas', 'distances']
                )
            )
            
            # Format results
            chunks = []
            if results['documents'] and len(results['documents']) > 0:
                documents = results['documents'][0]
                metadatas = results['metadatas'][0]
                distances = results['distances'][0]
                
                for i, (doc, metadata, distance) in enumerate(zip(documents, metadatas, distances)):
                    chunk = {
                        'id': i + 1,  # Simple numbering for citations
                        'text': doc,
                        'document': metadata.get('document', 'unknown'),
                        'page': metadata.get('page', 0),
                        'images': json.loads(metadata.get('images', '[]')),
                        'similarity': 1 - distance,  # Convert distance to similarity
                        'word_count': metadata.get('word_count', 0)
                    }
                    chunks.append(chunk)
                
                # Sort by similarity
                chunks.sort(key=lambda x: x['similarity'], reverse=True)
            
            # Cache results for future queries
            performance_optimizer.cache_result(cache_key, chunks, ttl_seconds=1800)  # 30 minutes
            
            logger.info(f"Found {len(chunks)} relevant chunks for query: {query[:50]}...")
            return chunks
            
        except Exception as e:
            logger.error(f"❌ Vector search failed: {e}")
            return []
    
    @timed("delete_document")
    def delete_document(self, document_name: str) -> int:
        """
        Delete all chunks for a specific document with optimization
        
        Args:
            document_name: Name of the document to delete
            
        Returns:
            Number of chunks deleted
        """
        try:
            # Get all chunks for this document
            results = self.collection.get(
                where={"document": document_name},
                include=['ids']
            )
            
            if results['ids']:
                # Delete in batches for large documents
                batch_size = 100
                total_deleted = 0
                
                for i in range(0, len(results['ids']), batch_size):
                    batch_ids = results['ids'][i:i + batch_size]
                    self.collection.delete(ids=batch_ids)
                    total_deleted += len(batch_ids)
                
                # Clear related cache entries
                self._clear_document_cache(document_name)
                
                logger.info(f"✅ Deleted {total_deleted} chunks for document: {document_name}")
                return total_deleted
            
            return 0
            
        except Exception as e:
            logger.error(f"❌ Failed to delete document chunks: {e}")
            return 0
    
    def _clear_document_cache(self, document_name: str):
        """Clear cache entries related to a document"""
        # Clear embedding cache entries for this document
        # This is a simple implementation - could be more sophisticated
        cache_keys_to_remove = []
        for key in performance_optimizer.cache.keys():
            if key.startswith('search:') and document_name in str(performance_optimizer.cache[key]):
                cache_keys_to_remove.append(key)
        
        for key in cache_keys_to_remove:
            del performance_optimizer.cache[key]
            del performance_optimizer.cache_ttl[key]
    
    def get_collection_stats(self) -> Dict:
        """Get detailed statistics about the collection"""
        try:
            count = self.collection.count()
            
            # Get sample of documents for analysis
            sample_results = self.collection.get(
                limit=min(100, count),
                include=['metadatas']
            )
            
            # Analyze document distribution
            doc_distribution = {}
            total_word_count = 0
            
            if sample_results['metadatas']:
                for metadata in sample_results['metadatas']:
                    doc_name = metadata.get('document', 'unknown')
                    word_count = metadata.get('word_count', 0)
                    
                    if doc_name in doc_distribution:
                        doc_distribution[doc_name] += 1
                    else:
                        doc_distribution[doc_name] = 1
                    
                    total_word_count += word_count
            
            return {
                "total_chunks": count,
                "collection_name": "ragdemo_documents",
                "embedding_model": "BAAI/bge-base-en-v1.5",
                "embedding_dimensions": 768,
                "documents_count": len(doc_distribution),
                "avg_word_count": round(total_word_count / len(sample_results['metadatas']) if sample_results['metadatas'] else 0),
                "cache_entries": len(self._embedding_cache),
                "top_documents": sorted(doc_distribution.items(), key=lambda x: x[1], reverse=True)[:5]
            }
        except Exception as e:
            logger.error(f"❌ Failed to get collection stats: {e}")
            return {"total_chunks": 0, "error": str(e)}
    
    async def benchmark_search(self, query: str, iterations: int = 10) -> Dict:
        """Benchmark search performance"""
        times = []
        
        for i in range(iterations):
            start_time = asyncio.get_event_loop().time()
            await self.search(query, limit=5)
            end_time = asyncio.get_event_loop().time()
            times.append(end_time - start_time)
        
        return {
            "query": query,
            "iterations": iterations,
            "avg_time_ms": round(np.mean(times) * 1000, 2),
            "min_time_ms": round(np.min(times) * 1000, 2),
            "max_time_ms": round(np.max(times) * 1000, 2),
            "std_dev_ms": round(np.std(times) * 1000, 2)
        }