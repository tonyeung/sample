"""Data management components for the Multi-Agent System"""

from .knowledge_base import HybridSearchKnowledgeBase, Document, SearchResult
from .ingestion import DataIngestionPipeline

__all__ = [
    'HybridSearchKnowledgeBase',
    'Document',
    'SearchResult',
    'DataIngestionPipeline'
]
