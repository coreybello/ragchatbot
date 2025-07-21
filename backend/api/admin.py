"""
Admin API endpoints for document management and configuration
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Optional
import os
import json
from datetime import datetime

from backend.models.database import get_db, Document, update_config_value, get_config_value
from backend.utils.auth import admin_required
from backend.core.pdf_processor import PDFProcessor
from backend.core.vector_store import VectorStore
from backend.models.database import SessionLocal

router = APIRouter()

class ConfigRequest(BaseModel):
    chunk_size: int
    chunk_overlap: int

class PromptRequest(BaseModel):
    prompt: str

class ModelConfigRequest(BaseModel):
    temperature: float
    top_p: float

class DocumentResponse(BaseModel):
    id: int
    name: str
    size: str
    date: str
    chunks: int
    images: int

class DashboardDataResponse(BaseModel):
    documents: List[DocumentResponse]
    config: dict

# Initialize processors
pdf_processor = PDFProcessor()
vector_store = VectorStore()

@router.get("/admin/dashboard-data")
async def get_dashboard_data(
    db: SessionLocal = Depends(get_db),
    current_user: dict = Depends(admin_required)
):
    """Get all admin dashboard data in one request"""
    
    # Get all documents
    documents = db.query(Document).filter(Document.is_active == True).all()
    
    # Format document data
    doc_list = []
    for doc in documents:
        doc_list.append(DocumentResponse(
            id=doc.id,
            name=doc.name,
            size=f"{doc.size_bytes / (1024*1024):.1f} MB" if doc.size_bytes > 1024*1024 else f"{doc.size_bytes / 1024:.1f} KB",
            date=doc.upload_date,
            chunks=doc.chunks_count,
            images=doc.images_count
        ))
    
    # Get current configuration
    config = {
        "system_prompt": get_config_value(db, "system_prompt", ""),
        "chunk_size": int(get_config_value(db, "chunk_size", "512")),
        "chunk_overlap": int(get_config_value(db, "chunk_overlap", "50")),
        "temperature": float(get_config_value(db, "temperature", "0.7")),
        "top_p": float(get_config_value(db, "top_p", "1.0"))
    }
    
    return DashboardDataResponse(
        documents=doc_list,
        config=config
    )

@router.post("/ingest")
async def ingest_document(
    pdf_file: UploadFile = File(...),
    force_reprocess: bool = Form(False),
    current_user: dict = Depends(admin_required),
    db: SessionLocal = Depends(get_db)
):
    """
    Ingest a PDF document into the knowledge base
    """
    
    # Validate file type
    if not pdf_file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Check file size
    if pdf_file.size > 50 * 1024 * 1024:  # 50MB limit
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 50MB")
    
    try:
        # Save uploaded file temporarily
        upload_dir = "./data/pdfs"
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, pdf_file.filename)
        
        with open(file_path, "wb") as f:
            content = await pdf_file.read()
            f.write(content)
        
        # Check if document already exists
        existing_doc = db.query(Document).filter(Document.name == pdf_file.filename).first()
        if existing_doc and not force_reprocess:
            raise HTTPException(
                status_code=409, 
                detail="Document already exists. Use force_reprocess=true to reprocess."
            )
        
        # Process PDF
        chunks, images_count = pdf_processor.process_pdf(file_path, pdf_file.filename)
        
        # Add chunks to vector store
        chunks_added = vector_store.add_document_chunks(chunks)
        
        # Update or create document record
        if existing_doc:
            # Delete old chunks from vector store
            vector_store.delete_document(pdf_file.filename)
            
            # Update existing document
            existing_doc.size_bytes = pdf_file.size
            existing_doc.upload_date = datetime.now().strftime("%Y-%m-%d")
            existing_doc.chunks_count = chunks_added
            existing_doc.images_count = images_count
            existing_doc.is_active = True
        else:
            # Create new document record
            new_doc = Document(
                name=pdf_file.filename,
                size_bytes=pdf_file.size,
                upload_date=datetime.now().strftime("%Y-%m-%d"),
                chunks_count=chunks_added,
                images_count=images_count,
                is_active=True
            )
            db.add(new_doc)
        
        db.commit()
        
        return {
            "status": "success",
            "document_id": existing_doc.id if existing_doc else None,
            "chunks_created": chunks_added,
            "images_extracted": images_count
        }
        
    except Exception as e:
        # Clean up temporary file on error
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Document processing failed: {str(e)}")

@router.get("/documents")
async def list_documents(
    current_user: dict = Depends(admin_required),
    db: SessionLocal = Depends(get_db)
):
    """List all indexed documents"""
    
    documents = db.query(Document).filter(Document.is_active == True).all()
    
    doc_list = []
    for doc in documents:
        doc_list.append({
            "id": doc.id,
            "name": doc.name,
            "size": f"{doc.size_bytes / (1024*1024):.1f} MB" if doc.size_bytes > 1024*1024 else f"{doc.size_bytes / 1024:.1f} KB",
            "date": doc.upload_date,
            "chunks": doc.chunks_count,
            "images": doc.images_count
        })
    
    return doc_list

@router.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: int,
    current_user: dict = Depends(admin_required),
    db: SessionLocal = Depends(get_db)
):
    """Delete a document from the knowledge base"""
    
    # Find document
    document = db.query(Document).filter(Document.id == doc_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        # Delete from vector store
        chunks_deleted = vector_store.delete_document(document.name)
        
        # Mark document as inactive
        document.is_active = False
        db.commit()
        
        return {
            "status": "success",
            "chunks_deleted": chunks_deleted,
            "images_deleted": document.images_count  # Images remain on disk for now
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document deletion failed: {str(e)}")

@router.post("/re-index")
async def reindex_knowledge_base(
    current_user: dict = Depends(admin_required),
    db: SessionLocal = Depends(get_db)
):
    """Trigger full re-indexing of all documents"""
    
    try:
        # Clear vector store
        vector_store.clear_all()
        
        # Get all active documents
        documents = db.query(Document).filter(Document.is_active == True).all()
        
        total_chunks = 0
        total_images = 0
        
        # Re-process each document
        for document in documents:
            pdf_path = os.path.join("./data/pdfs", document.name)
            
            if os.path.exists(pdf_path):
                # Re-process PDF
                chunks, images_count = pdf_processor.process_pdf(pdf_path, document.name)
                
                # Add to vector store
                chunks_added = vector_store.add_document_chunks(chunks)
                
                # Update document record
                document.chunks_count = chunks_added
                document.images_count = images_count
                
                total_chunks += chunks_added
                total_images += images_count
        
        db.commit()
        
        return {
            "status": "processing",
            "message": "Re-indexing complete",
            "job_id": f"reindex-{int(datetime.now().timestamp())}",
            "total_chunks": total_chunks,
            "total_images": total_images,
            "documents_processed": len(documents)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Re-indexing failed: {str(e)}")

@router.post("/config/prompt")
async def update_system_prompt(
    request: PromptRequest,
    current_user: dict = Depends(admin_required),
    db: SessionLocal = Depends(get_db)
):
    """Update system prompt"""
    
    try:
        update_config_value(db, "system_prompt", request.prompt)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update prompt: {str(e)}")

@router.post("/config/pipeline")
async def update_pipeline_config(
    request: ConfigRequest,
    current_user: dict = Depends(admin_required),
    db: SessionLocal = Depends(get_db)
):
    """Update pipeline configuration"""
    
    # Validate parameters
    if request.chunk_size < 100 or request.chunk_size > 2000:
        raise HTTPException(status_code=400, detail="Chunk size must be between 100 and 2000")
    
    if request.chunk_overlap < 0 or request.chunk_overlap >= request.chunk_size:
        raise HTTPException(status_code=400, detail="Chunk overlap must be between 0 and chunk_size")
    
    try:
        update_config_value(db, "chunk_size", str(request.chunk_size))
        update_config_value(db, "chunk_overlap", str(request.chunk_overlap))
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update configuration: {str(e)}")

@router.post("/config/model")
async def update_model_config(
    request: ModelConfigRequest,
    current_user: dict = Depends(admin_required),
    db: SessionLocal = Depends(get_db)
):
    """Update model generation parameters"""
    
    # Validate parameters
    if not 0 <= request.temperature <= 2:
        raise HTTPException(status_code=400, detail="Temperature must be between 0 and 2")
    
    if not 0 <= request.top_p <= 1:
        raise HTTPException(status_code=400, detail="Top-p must be between 0 and 1")
    
    try:
        update_config_value(db, "temperature", str(request.temperature))
        update_config_value(db, "top_p", str(request.top_p))
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update model configuration: {str(e)}")