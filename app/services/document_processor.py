import logging
import tempfile
import os
import uuid
import shutil
from typing import List, Dict, Any, Optional
from pathlib import Path

from llama_index.core.indices.vector_store import VectorStoreIndex
from llama_index.core import Settings
from llama_index.core.schema import Document
from llama_index.core.node_parser import SentenceSplitter
from llama_index.legacy.embeddings import HuggingFaceEmbedding
from llama_index.readers.file import PDFReader, DocxReader, MarkdownReader

from app.services.storage import S3StorageService
from app.services.vector_store import QdrantService

logger = logging.getLogger(__name__)


class TextFileReader:
    """Simple reader for text files"""
    
    def load_data(self, file: Path) -> List[Document]:
        """Load text file and return as Document"""
        try:
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return [Document(text=content)]
        except Exception as e:
            logger.error(f"Failed to read text file {file}: {e}")
            return []


class DocumentProcessor:
    """Service for processing documents with LlamaIndex"""
    
    def __init__(self, s3_service: S3StorageService, qdrant_service: QdrantService):
        """Initialize document processor"""
        self.s3_service = s3_service
        self.qdrant_service = qdrant_service
        
        # Initialize embedding model
        self.embedding_model = HuggingFaceEmbedding(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        # Set embedding model for LlamaIndex
        Settings.embed_model = self.embedding_model
        
        # Initialize node parser
        self.node_parser = SentenceSplitter(
            chunk_size=512,
            chunk_overlap=50
        )
        
        # File readers
        self.readers = {
            '.pdf': PDFReader(),
            '.docx': DocxReader(),
            '.txt': TextFileReader(),
            '.md': MarkdownReader()
        }
    
    def download_file_from_s3(self, s3_key: str) -> Optional[Path]:
        """Download file from S3 to temporary location"""
        try:
            # Get file from S3
            response = self.s3_service.s3_client.get_object(
                Bucket=self.s3_service.bucket_name,
                Key=s3_key
            )
            
            # Create temporary file
            file_extension = Path(s3_key).suffix
            with tempfile.NamedTemporaryFile(
                suffix=file_extension, 
                delete=False
            ) as temp_file:
                temp_file.write(response['Body'].read())
                temp_path = Path(temp_file.name)
            
            logger.info(f"Downloaded file from S3: {s3_key} -> {temp_path}")
            return temp_path
            
        except Exception as e:
            logger.error(f"Failed to download file from S3: {e}")
            return None
    
    def read_document(self, file_path: Path) -> Optional[List[Document]]:
        """Read document using appropriate reader"""
        try:
            file_extension = file_path.suffix.lower()
            
            if file_extension not in self.readers:
                logger.error(f"Unsupported file type: {file_extension}")
                return None
            
            reader = self.readers[file_extension]
            
            # All readers now expect file path
            documents = reader.load_data(file=file_path)
            
            # Check if documents were loaded successfully
            if not documents:
                logger.error(f"No documents loaded from {file_path}")
                return None
                
            logger.info(f"Read {len(documents)} documents from {file_path}")
            return documents
            
        except Exception as e:
            logger.error(f"Failed to read document {file_path}: {e}")
            return None
    
    def process_document(self, s3_key: str, filename: str) -> bool:
        """Process document: download, parse, and store in vector database"""
        try:
            # Download file from S3
            temp_file_path = self.download_file_from_s3(s3_key)
            if not temp_file_path:
                return False
            
            try:
                # Read document
                documents = self.read_document(temp_file_path)
                if not documents:
                    return False
                
                # Create vector store index
                index = VectorStoreIndex.from_documents(
                    documents,
                    transformations=[self.node_parser]
                )
                
                # Get nodes with embeddings
                nodes = index.docstore.docs.values()
                
                # Prepare documents for Qdrant
                qdrant_documents = []
                for i, node in enumerate(nodes):
                    # Create embedding for the node text
                    try:
                        embedding = self.embedding_model.get_text_embedding(node.text)
                        logger.debug(f"Created embedding for chunk {i}: {len(embedding)} dimensions")
                    except Exception as e:
                        logger.error(f"Failed to create embedding for chunk {i}: {e}")
                        continue
                    
                    # Generate unique UUID for Qdrant point ID
                    point_id = str(uuid.uuid4())
                    
                    qdrant_doc = {
                        'id': point_id,
                        'content': node.text,
                        'vector': embedding,
                        'metadata': {
                            'filename': filename,
                            's3_key': s3_key,
                            'chunk_id': i,
                            'chunk_size': len(node.text),
                            'original_id': f"{s3_key}_{i}"  # Keep original ID in metadata
                        },
                        'source': s3_key,
                        'filename': filename
                    }
                    qdrant_documents.append(qdrant_doc)
                
                if not qdrant_documents:
                    logger.error("No documents with valid embeddings to store")
                    return False
                
                # Store in Qdrant
                success = self.qdrant_service.add_documents(qdrant_documents)
                
                if success:
                    logger.info(
                        f"Successfully processed document: {filename} "
                        f"({len(qdrant_documents)} chunks)"
                    )
                else:
                    logger.error(f"Failed to store document in Qdrant: {filename}")
                
                return success
                
            finally:
                # Clean up temporary file
                if temp_file_path.exists():
                    temp_file_path.unlink()
                    logger.info(f"Cleaned up temporary file: {temp_file_path}")
            
        except Exception as e:
            logger.error(f"Failed to process document {filename}: {e}")
            return False 