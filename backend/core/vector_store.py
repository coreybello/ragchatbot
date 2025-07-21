"""
ChromaDB vector store for document embeddings and semantic search
"""
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import json
import logging
from typing import List, Dict, Optional
import uuid

from backend.core.config import get_settings

logger = logging.getLogger(__name__)

class VectorStore:
    """ChromaDB-based vector store for document chunks"""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = None
        self.collection = None
        self.embedding_model = None
        self._initialize()
    
    def _initialize(self):
        """Initialize ChromaDB client and collection"""
        try:
            # Create ChromaDB client with persistence
            self.client = chromadb.PersistentClient(
                path=self.settings.chroma_persist_dir
            )
            
            # Load embedding model
            logger.info("Loading BAAI/bge-base-en-v1.5 embedding model...")
            self.embedding_model = SentenceTransformer('BAAI/bge-base-en-v1.5')
            logger.info("✅ Embedding model loaded")
            
            # Get or create collection
            try:
                self.collection = self.client.get_collection("ragdemo_documents")
                logger.info("✅ Connected to existing ChromaDB collection")
            except ValueError:
                # Collection doesn't exist, create it
                self.collection = self.client.create_collection(
                    name="ragdemo_documents",
                    metadata={"hnsw:space": "cosine"}
                )
                logger.info("✅ Created new ChromaDB collection")
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize vector store: {e}")
            raise RuntimeError(f"Vector store initialization failed: {e}")
    
    def add_document_chunks(self, chunks: List[Dict]) -> int:
        """
        Add document chunks to the vector store
        
        Args:
            chunks: List of chunk dictionaries with keys:
                - id: unique chunk identifier
                - text: chunk text content
                - document: source document name
                - page: page number
                - images: list of associated image filenames
        
        Returns:
            Number of chunks added
        """
        if not chunks:
            return 0
        
        try:
            # Prepare data for ChromaDB
            ids = []
            texts = []
            embeddings = []
            metadatas = []
            
            for chunk in chunks:
                chunk_id = chunk.get('id', str(uuid.uuid4()))
                text = chunk['text']
                
                # Generate embedding
                embedding = self.embedding_model.encode(text).tolist()
                
                ids.append(chunk_id)
                texts.append(text)
                embeddings.append(embedding)
                metadatas.append({
                    "document": chunk.get('document', 'unknown'),
                    "page": chunk.get('page', 0),
                    "images": json.dumps(chunk.get('images', []))
                })
            
            # Add to collection
            self.collection.add(
                ids=ids,
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas
            )
            
            logger.info(f"✅ Added {len(chunks)} chunks to vector store")
            return len(chunks)
            
        except Exception as e:
            logger.error(f"❌ Failed to add chunks to vector store: {e}")
            raise RuntimeError(f"Failed to add document chunks: {e}")
    
    async def search(self, query: str, limit: int = 5) -> List[Dict]:
        """
        Semantic search for relevant document chunks
        
        Args:
            query: Search query string
            limit: Maximum number of results to return
            
        Returns:
            List of relevant chunk dictionaries
        """
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode(query).tolist()
            
            # Search in ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                include=['documents', 'metadatas', 'distances']
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
                        'similarity': 1 - distance  # Convert distance to similarity
                    }
                    chunks.append(chunk)
            
            logger.info(f"Found {len(chunks)} relevant chunks for query: {query[:50]}...")
            return chunks
            
        except Exception as e:
            logger.error(f"❌ Vector search failed: {e}")
            return []
    
    def delete_document(self, document_name: str) -> int:
        """
        Delete all chunks for a specific document
        
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
                # Delete the chunks
                self.collection.delete(ids=results['ids'])
                logger.info(f"✅ Deleted {len(results['ids'])} chunks for document: {document_name}")
                return len(results['ids'])
            
            return 0
            
        except Exception as e:
            logger.error(f"❌ Failed to delete document chunks: {e}")
            return 0
    
    def clear_all(self):
        """Clear all documents from the vector store"""
        try:
            # Delete the collection and recreate it
            self.client.delete_collection("ragdemo_documents")
            self.collection = self.client.create_collection(
                name="ragdemo_documents",
                metadata={"hnsw:space": "cosine"}
            )
            logger.info("✅ Cleared all documents from vector store")
            
        except Exception as e:
            logger.error(f"❌ Failed to clear vector store: {e}")
            raise RuntimeError(f"Failed to clear vector store: {e}")
    
    def get_collection_stats(self) -> Dict:
        """Get statistics about the collection"""
        try:
            count = self.collection.count()
            return {
                "total_chunks": count,
                "collection_name": "ragdemo_documents",
                "embedding_model": "BAAI/bge-base-en-v1.5",
                "embedding_dimensions": 768
            }
        except Exception as e:
            logger.error(f"❌ Failed to get collection stats: {e}")
            return {"total_chunks": 0}