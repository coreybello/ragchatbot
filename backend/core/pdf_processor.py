"""
PDF processing module for text and image extraction
Uses PyMuPDF for reliable PDF parsing with image support
"""
import fitz  # PyMuPDF
import os
import json
import hashlib
from typing import List, Dict, Tuple
import logging
from PIL import Image
import io

from backend.core.config import get_settings

logger = logging.getLogger(__name__)

class PDFProcessor:
    """PDF processor for extracting text chunks and images"""
    
    def __init__(self):
        self.settings = get_settings()
        self.chunk_size = self.settings.chunk_size
        self.chunk_overlap = self.settings.chunk_overlap
    
    def process_pdf(self, pdf_path: str, document_name: str = None) -> Tuple[List[Dict], int]:
        """
        Process a PDF file and extract text chunks with images
        
        Args:
            pdf_path: Path to the PDF file
            document_name: Name for the document (optional)
            
        Returns:
            Tuple of (chunks_list, images_count)
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        if not document_name:
            document_name = os.path.basename(pdf_path)
        
        logger.info(f"Processing PDF: {document_name}")
        
        try:
            # Open PDF document
            pdf_document = fitz.open(pdf_path)
            
            # Extract text and images
            all_text = ""
            images_extracted = 0
            page_texts = []
            
            for page_num in range(pdf_document.page_count):
                page = pdf_document[page_num]
                
                # Extract text from page
                page_text = page.get_text()
                page_texts.append({
                    'page': page_num + 1,
                    'text': page_text
                })
                all_text += f"\\n\\nPage {page_num + 1}:\\n{page_text}"
                
                # Extract images from page
                image_list = page.get_images()
                for img_index, img in enumerate(image_list):
                    try:
                        # Get image data
                        xref = img[0]
                        base_image = pdf_document.extract_image(xref)
                        image_bytes = base_image["image"]
                        image_ext = base_image["ext"]
                        
                        # Generate unique filename
                        image_hash = hashlib.md5(image_bytes).hexdigest()[:8]
                        image_filename = f"{document_name}_p{page_num+1}_{image_hash}.{image_ext}"
                        image_path = os.path.join(self.settings.image_dir, image_filename)
                        
                        # Save image
                        with open(image_path, "wb") as img_file:
                            img_file.write(image_bytes)
                        
                        images_extracted += 1
                        logger.debug(f"Extracted image: {image_filename}")
                        
                    except Exception as e:
                        logger.warning(f"Failed to extract image {img_index} from page {page_num + 1}: {e}")
            
            pdf_document.close()
            
            # Create text chunks
            chunks = self._create_chunks(all_text, page_texts, document_name)
            
            logger.info(f"✅ Processed {document_name}: {len(chunks)} chunks, {images_extracted} images")
            
            return chunks, images_extracted
            
        except Exception as e:
            logger.error(f"❌ Failed to process PDF {document_name}: {e}")
            raise RuntimeError(f"PDF processing failed: {e}")
    
    def _create_chunks(self, full_text: str, page_texts: List[Dict], document_name: str) -> List[Dict]:
        """
        Create overlapping text chunks from extracted text
        
        Args:
            full_text: Complete text from PDF
            page_texts: List of page-specific text data
            document_name: Source document name
            
        Returns:
            List of chunk dictionaries
        """
        chunks = []
        
        # Simple word-based chunking
        words = full_text.split()
        
        if len(words) <= self.chunk_size:
            # Document is small enough to be a single chunk
            chunks.append({
                'id': f"{document_name}_chunk_1",
                'text': full_text.strip(),
                'document': document_name,
                'page': 1,
                'images': self._get_page_images(document_name, 1),
                'word_count': len(words)
            })
            return chunks
        
        # Create overlapping chunks
        chunk_id = 1
        start_idx = 0
        
        while start_idx < len(words):
            # Get chunk words
            end_idx = min(start_idx + self.chunk_size, len(words))
            chunk_words = words[start_idx:end_idx]
            chunk_text = ' '.join(chunk_words)
            
            # Determine primary page for this chunk
            chunk_page = self._estimate_page_number(start_idx, len(words), len(page_texts))
            
            # Get images associated with this chunk's pages
            chunk_images = self._get_chunk_images(document_name, chunk_page)
            
            chunks.append({
                'id': f"{document_name}_chunk_{chunk_id}",
                'text': chunk_text.strip(),
                'document': document_name,
                'page': chunk_page,
                'images': chunk_images,
                'word_count': len(chunk_words)
            })
            
            chunk_id += 1
            
            # Move start position (with overlap)
            if end_idx >= len(words):
                break
            start_idx = end_idx - self.chunk_overlap
        
        return chunks
    
    def _estimate_page_number(self, word_index: int, total_words: int, total_pages: int) -> int:
        """Estimate which page a word index corresponds to"""
        if total_words == 0:
            return 1
        
        # Simple linear estimation
        estimated_page = int((word_index / total_words) * total_pages) + 1
        return min(max(estimated_page, 1), total_pages)
    
    def _get_page_images(self, document_name: str, page_num: int) -> List[str]:
        """Get list of image filenames for a specific page"""
        images = []
        try:
            # Look for images with this document and page pattern
            for filename in os.listdir(self.settings.image_dir):
                if filename.startswith(f"{document_name}_p{page_num}_"):
                    images.append(filename)
        except Exception as e:
            logger.debug(f"Could not scan images directory: {e}")
        
        return images
    
    def _get_chunk_images(self, document_name: str, primary_page: int) -> List[str]:
        """Get images for a chunk (including adjacent pages for overlap)"""
        images = []
        
        # Get images from primary page and adjacent pages
        for page_offset in [-1, 0, 1]:
            page_num = primary_page + page_offset
            if page_num > 0:
                page_images = self._get_page_images(document_name, page_num)
                images.extend(page_images)
        
        return list(set(images))  # Remove duplicates
    
    def validate_pdf(self, pdf_path: str) -> bool:
        """
        Validate that a file is a readable PDF
        
        Args:
            pdf_path: Path to the file to validate
            
        Returns:
            True if valid PDF, False otherwise
        """
        try:
            pdf_document = fitz.open(pdf_path)
            page_count = pdf_document.page_count
            pdf_document.close()
            
            return page_count > 0
            
        except Exception as e:
            logger.warning(f"PDF validation failed for {pdf_path}: {e}")
            return False
    
    def get_pdf_info(self, pdf_path: str) -> Dict:
        """
        Get basic information about a PDF file
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary with PDF information
        """
        try:
            pdf_document = fitz.open(pdf_path)
            
            info = {
                "filename": os.path.basename(pdf_path),
                "page_count": pdf_document.page_count,
                "file_size": os.path.getsize(pdf_path),
                "metadata": pdf_document.metadata
            }
            
            pdf_document.close()
            return info
            
        except Exception as e:
            logger.error(f"Failed to get PDF info for {pdf_path}: {e}")
            return {"error": str(e)}