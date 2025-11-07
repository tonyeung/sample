"""Knowledge Base with Hybrid Search (Vector + Keyword)"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import logging
import json
import re
from collections import defaultdict
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class Document:
    """Represents a document in the knowledge base"""
    id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'content': self.content,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


@dataclass
class SearchResult:
    """Represents a search result"""
    document: Document
    score: float
    match_type: str  # 'vector', 'keyword', 'hybrid'
    matched_terms: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'document': self.document.to_dict(),
            'score': self.score,
            'match_type': self.match_type,
            'matched_terms': self.matched_terms
        }


class HybridSearchKnowledgeBase:
    """
    Knowledge base with hybrid search capabilities.

    Features:
    - Vector-based semantic search
    - Keyword-based search
    - Hybrid search combining both approaches
    - Document versioning
    - Metadata filtering
    """

    def __init__(
        self,
        embedding_dim: int = 384,  # Default dimension for embeddings
        index_name: str = "main_index"
    ):
        self.embedding_dim = embedding_dim
        self.index_name = index_name

        # Storage
        self.documents: Dict[str, Document] = {}
        self.keyword_index: Dict[str, List[str]] = defaultdict(list)  # word -> doc_ids
        self.vector_index: List[Tuple[str, List[float]]] = []  # (doc_id, embedding)

        # Statistics
        self.stats = {
            'total_documents': 0,
            'total_searches': 0,
            'last_indexed': None
        }

        logger.info(f"Initialized HybridSearchKnowledgeBase: {index_name}")

    async def ingest_document(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        doc_id: Optional[str] = None
    ) -> str:
        """Ingest a document into the knowledge base"""

        # Generate doc_id if not provided
        if not doc_id:
            doc_id = self._generate_doc_id(content)

        # Create document
        document = Document(
            id=doc_id,
            content=content,
            metadata=metadata or {}
        )

        # Generate embedding (simulated - in production use actual embedding model)
        embedding = await self._generate_embedding(content)
        document.embedding = embedding

        # Store document
        self.documents[doc_id] = document

        # Index for keyword search
        await self._index_keywords(doc_id, content)

        # Index for vector search
        if embedding:
            self.vector_index.append((doc_id, embedding))

        # Update stats
        self.stats['total_documents'] = len(self.documents)
        self.stats['last_indexed'] = datetime.now().isoformat()

        logger.info(f"Ingested document: {doc_id}")

        return doc_id

    async def ingest_documents_batch(
        self,
        documents: List[Dict[str, Any]]
    ) -> List[str]:
        """Ingest multiple documents at once"""
        doc_ids = []

        for doc in documents:
            doc_id = await self.ingest_document(
                content=doc.get('content', ''),
                metadata=doc.get('metadata', {}),
                doc_id=doc.get('id')
            )
            doc_ids.append(doc_id)

        logger.info(f"Ingested {len(doc_ids)} documents in batch")

        return doc_ids

    async def search(
        self,
        query: str,
        top_k: int = 5,
        search_type: str = "hybrid",  # 'vector', 'keyword', 'hybrid'
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        Search the knowledge base using hybrid search.

        Args:
            query: Search query
            top_k: Number of results to return
            search_type: Type of search ('vector', 'keyword', 'hybrid')
            filters: Metadata filters to apply

        Returns:
            List of SearchResult objects
        """
        self.stats['total_searches'] += 1

        logger.info(f"Searching with query: '{query}' (type: {search_type})")

        if search_type == "vector":
            results = await self._vector_search(query, top_k)
        elif search_type == "keyword":
            results = await self._keyword_search(query, top_k)
        else:  # hybrid
            results = await self._hybrid_search(query, top_k)

        # Apply filters if provided
        if filters:
            results = self._apply_filters(results, filters)

        return results[:top_k]

    async def _vector_search(self, query: str, top_k: int) -> List[SearchResult]:
        """Perform vector-based semantic search"""
        # Generate query embedding
        query_embedding = await self._generate_embedding(query)

        if not query_embedding or not self.vector_index:
            return []

        # Calculate cosine similarity with all documents
        scored_docs = []

        for doc_id, doc_embedding in self.vector_index:
            similarity = self._cosine_similarity(query_embedding, doc_embedding)
            scored_docs.append((doc_id, similarity))

        # Sort by similarity
        scored_docs.sort(key=lambda x: x[1], reverse=True)

        # Create search results
        results = []
        for doc_id, score in scored_docs[:top_k]:
            if doc_id in self.documents:
                results.append(SearchResult(
                    document=self.documents[doc_id],
                    score=score,
                    match_type='vector',
                    matched_terms=[]
                ))

        return results

    async def _keyword_search(self, query: str, top_k: int) -> List[SearchResult]:
        """Perform keyword-based search"""
        # Tokenize query
        query_terms = self._tokenize(query.lower())

        # Find matching documents
        doc_scores = defaultdict(float)
        matched_terms_per_doc = defaultdict(list)

        for term in query_terms:
            if term in self.keyword_index:
                for doc_id in self.keyword_index[term]:
                    doc_scores[doc_id] += 1.0
                    matched_terms_per_doc[doc_id].append(term)

        # Sort by score
        sorted_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)

        # Create search results
        results = []
        for doc_id, score in sorted_docs[:top_k]:
            if doc_id in self.documents:
                results.append(SearchResult(
                    document=self.documents[doc_id],
                    score=score / len(query_terms),  # Normalize
                    match_type='keyword',
                    matched_terms=matched_terms_per_doc[doc_id]
                ))

        return results

    async def _hybrid_search(self, query: str, top_k: int) -> List[SearchResult]:
        """Perform hybrid search combining vector and keyword approaches"""
        # Get results from both methods
        vector_results = await self._vector_search(query, top_k * 2)
        keyword_results = await self._keyword_search(query, top_k * 2)

        # Combine results with weighted scoring
        combined_scores = defaultdict(lambda: {'vector': 0.0, 'keyword': 0.0, 'doc': None, 'terms': []})

        # Add vector scores (weight: 0.6)
        for result in vector_results:
            doc_id = result.document.id
            combined_scores[doc_id]['vector'] = result.score * 0.6
            combined_scores[doc_id]['doc'] = result.document

        # Add keyword scores (weight: 0.4)
        for result in keyword_results:
            doc_id = result.document.id
            combined_scores[doc_id]['keyword'] = result.score * 0.4
            combined_scores[doc_id]['doc'] = result.document
            combined_scores[doc_id]['terms'] = result.matched_terms

        # Calculate final scores
        final_results = []
        for doc_id, scores in combined_scores.items():
            final_score = scores['vector'] + scores['keyword']
            final_results.append(SearchResult(
                document=scores['doc'],
                score=final_score,
                match_type='hybrid',
                matched_terms=scores['terms']
            ))

        # Sort by final score
        final_results.sort(key=lambda x: x.score, reverse=True)

        return final_results[:top_k]

    async def _index_keywords(self, doc_id: str, content: str):
        """Index document for keyword search"""
        terms = self._tokenize(content.lower())

        for term in set(terms):  # Use set to avoid duplicates
            self.keyword_index[term].append(doc_id)

    async def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text.
        This is a simplified version - in production, use actual embedding models
        like sentence-transformers, OpenAI embeddings, etc.
        """
        # Simulate embedding generation
        await asyncio.sleep(0.01)  # Simulate processing time

        # Simple hash-based embedding for demonstration
        # In production, replace with actual embedding model
        import hashlib
        import math

        # Create a deterministic pseudo-embedding
        hash_obj = hashlib.md5(text.encode())
        hash_bytes = hash_obj.digest()

        # Convert to float values
        embedding = []
        for i in range(0, len(hash_bytes), 2):
            if i + 1 < len(hash_bytes):
                val = (hash_bytes[i] * 256 + hash_bytes[i + 1]) / 65535.0
                embedding.append(val)

        # Pad or truncate to embedding_dim
        while len(embedding) < self.embedding_dim:
            embedding.append(0.0)
        embedding = embedding[:self.embedding_dim]

        # Normalize
        norm = math.sqrt(sum(x * x for x in embedding))
        if norm > 0:
            embedding = [x / norm for x in embedding]

        return embedding

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        if len(vec1) != len(vec2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        return max(0.0, min(1.0, dot_product))  # Clamp between 0 and 1

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into words"""
        # Simple tokenization - can be enhanced with stemming, lemmatization, etc.
        words = re.findall(r'\b\w+\b', text.lower())
        # Remove stop words (simplified list)
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        return [w for w in words if w not in stop_words and len(w) > 2]

    def _apply_filters(self, results: List[SearchResult], filters: Dict[str, Any]) -> List[SearchResult]:
        """Apply metadata filters to search results"""
        filtered = []

        for result in results:
            match = True
            for key, value in filters.items():
                if result.document.metadata.get(key) != value:
                    match = False
                    break

            if match:
                filtered.append(result)

        return filtered

    def _generate_doc_id(self, content: str) -> str:
        """Generate a unique document ID"""
        hash_obj = hashlib.sha256(f"{content}{datetime.now().isoformat()}".encode())
        return hash_obj.hexdigest()[:16]

    def get_document(self, doc_id: str) -> Optional[Document]:
        """Retrieve a document by ID"""
        return self.documents.get(doc_id)

    def delete_document(self, doc_id: str) -> bool:
        """Delete a document from the knowledge base"""
        if doc_id in self.documents:
            # Remove from documents
            del self.documents[doc_id]

            # Remove from keyword index
            for term, doc_ids in self.keyword_index.items():
                if doc_id in doc_ids:
                    doc_ids.remove(doc_id)

            # Remove from vector index
            self.vector_index = [(did, emb) for did, emb in self.vector_index if did != doc_id]

            # Update stats
            self.stats['total_documents'] = len(self.documents)

            logger.info(f"Deleted document: {doc_id}")
            return True

        return False

    def get_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics"""
        return {
            **self.stats,
            'keyword_index_size': len(self.keyword_index),
            'vector_index_size': len(self.vector_index)
        }

    async def export_knowledge_base(self) -> Dict[str, Any]:
        """Export knowledge base to dictionary"""
        return {
            'index_name': self.index_name,
            'documents': [doc.to_dict() for doc in self.documents.values()],
            'stats': self.get_stats()
        }
