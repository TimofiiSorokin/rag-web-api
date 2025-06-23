import logging
from pathlib import Path
from typing import List

from llama_index.legacy.schema import Document
from llama_index.legacy.node_parser import SimpleNodeParser
from llama_index.legacy.schema import BaseNode
from llama_index.legacy.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.legacy.readers.file.base import SimpleDirectoryReader

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Service for processing documents with LlamaIndex"""

    def __init__(self):
        """Initialize document processor"""
        self.embedding_model = None
        self.node_parser = SimpleNodeParser.from_defaults()
        self.setup_embedding_model()
        logger.info("DocumentProcessor initialized")

    def setup_embedding_model(
        self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    ):
        """Setup embedding model"""
        try:
            self.embedding_model = HuggingFaceEmbedding(model_name=model_name)
            logger.info(f"Embedding model setup: {model_name}")
        except Exception as e:
            logger.error(f"Failed to setup embedding model: {e}")
            raise

    def load_documents(self, file_path: str) -> List[Document]:
        """Load documents from file path"""
        try:
            path = Path(file_path)
            if not path.exists():
                logger.error(f"File not found: {file_path}")
                return []

            # Load documents using SimpleDirectoryReader
            reader = SimpleDirectoryReader(input_files=[str(path)])
            documents = reader.load_data()

            logger.info(f"Loaded {len(documents)} documents from {file_path}")
            return documents

        except Exception as e:
            logger.error(f"Error loading documents from {file_path}: {e}")
            return []

    def process_documents(self, documents: List[Document]) -> List[BaseNode]:
        """Process documents into nodes"""
        try:
            if not documents:
                logger.warning("No documents to process")
                return []

            # Parse documents into nodes
            nodes = self.node_parser.get_nodes_from_documents(documents)

            logger.info(f"Processed {len(documents)} documents into {len(nodes)} nodes")
            return nodes

        except Exception as e:
            logger.error(f"Error processing documents: {e}")
            return []

    def extract_text_from_nodes(self, nodes: List[BaseNode]) -> List[str]:
        """Extract text content from nodes"""
        try:
            texts = []
            for node in nodes:
                if hasattr(node, "text") and node.text:
                    texts.append(node.text)
                elif hasattr(node, "content") and node.content:
                    texts.append(node.content)
                else:
                    logger.warning(f"Node has no text content: {node}")

            logger.info(f"Extracted text from {len(texts)} nodes")
            return texts

        except Exception as e:
            logger.error(f"Error extracting text from nodes: {e}")
            return []

    def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings for text content"""
        try:
            if not self.embedding_model:
                logger.error("Embedding model not initialized")
                return []

            embeddings = []
            for text in texts:
                if text.strip():
                    embedding = self.embedding_model.get_text_embedding(text)
                    embeddings.append(embedding)
                else:
                    logger.warning("Skipping empty text for embedding")

            logger.info(f"Created embeddings for {len(embeddings)} texts")
            return embeddings

        except Exception as e:
            logger.error(f"Error creating embeddings: {e}")
            return []

    def process_file(self, file_path: str) -> dict:
        """Complete document processing pipeline"""
        try:
            # Load documents
            documents = self.load_documents(file_path)
            if not documents:
                return {"error": "No documents loaded"}

            # Process documents into nodes
            nodes = self.process_documents(documents)
            if not nodes:
                return {"error": "No nodes created"}

            # Extract text content
            texts = self.extract_text_from_nodes(nodes)
            if not texts:
                return {"error": "No text content extracted"}

            # Create embeddings
            embeddings = self.create_embeddings(texts)
            if not embeddings:
                return {"error": "No embeddings created"}

            return {
                "documents": documents,
                "nodes": nodes,
                "texts": texts,
                "embeddings": embeddings,
                "file_path": file_path,
            }

        except Exception as e:
            logger.error(f"Error in document processing pipeline: {e}")
            return {"error": str(e)}
