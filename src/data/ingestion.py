"""Data Ingestion Pipeline for Multi-Agent System"""

from typing import List, Dict, Any, Optional
import asyncio
import logging
from pathlib import Path
import json

from .knowledge_base import HybridSearchKnowledgeBase, Document

logger = logging.getLogger(__name__)


class DataIngestionPipeline:
    """
    Pipeline for ingesting data from various sources into the knowledge base.

    Supports:
    - Text files
    - JSON documents
    - Raw text input
    - Batch processing
    """

    def __init__(self, knowledge_base: HybridSearchKnowledgeBase):
        self.knowledge_base = knowledge_base
        self.ingestion_stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0
        }

        logger.info("Initialized DataIngestionPipeline")

    async def ingest_text(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        chunk_size: Optional[int] = None
    ) -> List[str]:
        """
        Ingest raw text into the knowledge base.

        Args:
            text: Text content to ingest
            metadata: Metadata to attach to the document
            chunk_size: If provided, split text into chunks of this size

        Returns:
            List of document IDs created
        """
        doc_ids = []

        try:
            if chunk_size:
                # Split into chunks
                chunks = self._split_text(text, chunk_size)
                for i, chunk in enumerate(chunks):
                    chunk_metadata = {
                        **(metadata or {}),
                        'chunk_index': i,
                        'total_chunks': len(chunks)
                    }
                    doc_id = await self.knowledge_base.ingest_document(
                        content=chunk,
                        metadata=chunk_metadata
                    )
                    doc_ids.append(doc_id)
            else:
                # Ingest as single document
                doc_id = await self.knowledge_base.ingest_document(
                    content=text,
                    metadata=metadata
                )
                doc_ids.append(doc_id)

            self.ingestion_stats['successful'] += len(doc_ids)
            self.ingestion_stats['total_processed'] += 1

            logger.info(f"Ingested text into {len(doc_ids)} documents")

        except Exception as e:
            logger.error(f"Error ingesting text: {str(e)}")
            self.ingestion_stats['failed'] += 1

        return doc_ids

    async def ingest_file(
        self,
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        Ingest a file into the knowledge base.

        Args:
            file_path: Path to the file
            metadata: Additional metadata

        Returns:
            List of document IDs created
        """
        path = Path(file_path)

        if not path.exists():
            logger.error(f"File not found: {file_path}")
            self.ingestion_stats['failed'] += 1
            return []

        # Add file metadata
        file_metadata = {
            'filename': path.name,
            'file_type': path.suffix,
            'file_size': path.stat().st_size,
            **(metadata or {})
        }

        try:
            if path.suffix == '.json':
                return await self._ingest_json_file(path, file_metadata)
            elif path.suffix in ['.txt', '.md', '.rst']:
                return await self._ingest_text_file(path, file_metadata)
            else:
                logger.warning(f"Unsupported file type: {path.suffix}")
                self.ingestion_stats['failed'] += 1
                return []

        except Exception as e:
            logger.error(f"Error ingesting file {file_path}: {str(e)}")
            self.ingestion_stats['failed'] += 1
            return []

    async def _ingest_text_file(
        self,
        path: Path,
        metadata: Dict[str, Any]
    ) -> List[str]:
        """Ingest a text file"""
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        return await self.ingest_text(content, metadata)

    async def _ingest_json_file(
        self,
        path: Path,
        metadata: Dict[str, Any]
    ) -> List[str]:
        """Ingest a JSON file"""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        doc_ids = []

        # Handle different JSON structures
        if isinstance(data, list):
            # List of documents
            for item in data:
                if isinstance(item, dict):
                    content = item.get('content', json.dumps(item))
                    item_metadata = {
                        **metadata,
                        **item.get('metadata', {})
                    }
                else:
                    content = str(item)
                    item_metadata = metadata

                doc_id = await self.knowledge_base.ingest_document(
                    content=content,
                    metadata=item_metadata
                )
                doc_ids.append(doc_id)

        elif isinstance(data, dict):
            # Single document or structured data
            if 'content' in data:
                content = data['content']
                doc_metadata = {
                    **metadata,
                    **data.get('metadata', {})
                }
            else:
                content = json.dumps(data, indent=2)
                doc_metadata = metadata

            doc_id = await self.knowledge_base.ingest_document(
                content=content,
                metadata=doc_metadata
            )
            doc_ids.append(doc_id)

        self.ingestion_stats['successful'] += len(doc_ids)
        self.ingestion_stats['total_processed'] += 1

        return doc_ids

    async def ingest_directory(
        self,
        directory_path: str,
        recursive: bool = True,
        file_patterns: Optional[List[str]] = None
    ) -> List[str]:
        """
        Ingest all files from a directory.

        Args:
            directory_path: Path to the directory
            recursive: Whether to process subdirectories
            file_patterns: List of file patterns to include (e.g., ['*.txt', '*.md'])

        Returns:
            List of all document IDs created
        """
        path = Path(directory_path)

        if not path.exists() or not path.is_dir():
            logger.error(f"Directory not found: {directory_path}")
            return []

        all_doc_ids = []
        patterns = file_patterns or ['*.txt', '*.md', '*.json']

        # Find all matching files
        files_to_process = []
        for pattern in patterns:
            if recursive:
                files_to_process.extend(path.rglob(pattern))
            else:
                files_to_process.extend(path.glob(pattern))

        logger.info(f"Found {len(files_to_process)} files to process")

        # Process each file
        for file_path in files_to_process:
            doc_ids = await self.ingest_file(
                str(file_path),
                metadata={'source_directory': directory_path}
            )
            all_doc_ids.extend(doc_ids)

        logger.info(f"Ingested {len(all_doc_ids)} documents from directory")

        return all_doc_ids

    async def ingest_batch(
        self,
        documents: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Ingest a batch of documents.

        Args:
            documents: List of dicts with 'content' and optional 'metadata'

        Returns:
            List of document IDs created
        """
        doc_ids = []

        for doc in documents:
            try:
                doc_id = await self.knowledge_base.ingest_document(
                    content=doc.get('content', ''),
                    metadata=doc.get('metadata', {})
                )
                doc_ids.append(doc_id)
                self.ingestion_stats['successful'] += 1

            except Exception as e:
                logger.error(f"Error ingesting document: {str(e)}")
                self.ingestion_stats['failed'] += 1

        self.ingestion_stats['total_processed'] += len(documents)

        logger.info(f"Batch ingested {len(doc_ids)}/{len(documents)} documents")

        return doc_ids

    def _split_text(self, text: str, chunk_size: int) -> List[str]:
        """Split text into chunks"""
        chunks = []
        words = text.split()

        current_chunk = []
        current_size = 0

        for word in words:
            current_chunk.append(word)
            current_size += len(word) + 1  # +1 for space

            if current_size >= chunk_size:
                chunks.append(' '.join(current_chunk))
                current_chunk = []
                current_size = 0

        # Add remaining words
        if current_chunk:
            chunks.append(' '.join(current_chunk))

        return chunks

    def get_stats(self) -> Dict[str, Any]:
        """Get ingestion statistics"""
        return {
            **self.ingestion_stats,
            'knowledge_base_stats': self.knowledge_base.get_stats()
        }

    def reset_stats(self):
        """Reset ingestion statistics"""
        self.ingestion_stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0
        }
        logger.info("Reset ingestion statistics")
