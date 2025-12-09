"""
RAG (Retrieval-Augmented Generation) Pipeline
Retrieves relevant context from approved materials for AI tutor responses
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.material import Material, MaterialTopic
from app.models.syllabus import Syllabus
from app.services.processing.embedding_service import EmbeddingService, get_embedding_service

logger = logging.getLogger(__name__)


class RAGPipeline:
    """
    Retrieval-Augmented Generation pipeline for the AI tutor.
    Retrieves relevant context from lecturer-approved materials only.
    """
    
    # Configuration
    DEFAULT_TOP_K = 5
    MAX_CONTEXT_LENGTH = 4000  # Characters
    
    def __init__(
        self,
        embedding_service: Optional[EmbeddingService] = None
    ):
        """
        Initialize the RAG pipeline.
        
        Args:
            embedding_service: Service for generating embeddings
        """
        self.embedding_service = embedding_service or get_embedding_service()
    
    def retrieve_context(
        self,
        db: Session,
        query: str,
        course_id: int,
        week_number: Optional[int] = None,
        top_k: int = DEFAULT_TOP_K,
        approved_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant context from materials for a query.
        
        Args:
            db: Database session
            query: User query
            course_id: Course ID to search within
            week_number: Optional specific week to focus on
            top_k: Number of context chunks to retrieve
            approved_only: Only use lecturer-approved materials
            
        Returns:
            List of context dictionaries with content and metadata
        """
        # Generate query embedding
        query_embedding = self.embedding_service.embed_text(query)
        
        # Get relevant materials
        materials = self._get_candidate_materials(
            db=db,
            course_id=course_id,
            week_number=week_number,
            approved_only=approved_only
        )
        
        if not materials:
            logger.info(f"No materials found for course {course_id}")
            return []
        
        # Score and rank materials
        scored_materials = []
        for material in materials:
            # Get material embedding
            material_embedding = self._get_embedding(material)
            
            # Calculate similarity
            similarity = self.embedding_service.compute_similarity(
                query_embedding,
                material_embedding
            )
            
            scored_materials.append({
                "material": material,
                "similarity": similarity
            })
        
        # Sort by similarity
        scored_materials.sort(key=lambda x: x["similarity"], reverse=True)
        
        # Build context chunks
        context_chunks = []
        total_length = 0
        
        for item in scored_materials[:top_k]:
            material = item["material"]
            
            # Extract relevant content
            content = self._extract_content(material, query)
            
            if total_length + len(content) > self.MAX_CONTEXT_LENGTH:
                # Truncate to fit
                remaining = self.MAX_CONTEXT_LENGTH - total_length
                if remaining > 200:
                    content = content[:remaining] + "..."
                else:
                    break
            
            context_chunks.append({
                "content": content,
                "source": material.source,
                "title": material.title,
                "url": material.url,
                "type": material.type,
                "similarity": item["similarity"],
                "material_id": material.id
            })
            
            total_length += len(content)
        
        return context_chunks
    
    def build_prompt_context(
        self,
        context_chunks: List[Dict[str, Any]],
        include_sources: bool = True
    ) -> str:
        """
        Build a formatted context string for LLM prompts.
        
        Args:
            context_chunks: Retrieved context chunks
            include_sources: Whether to include source citations
            
        Returns:
            Formatted context string
        """
        if not context_chunks:
            return ""
        
        context_parts = ["### Relevant Course Materials:\n"]
        
        for i, chunk in enumerate(context_chunks, 1):
            context_parts.append(f"**[{i}] {chunk['title']}**")
            if include_sources:
                context_parts.append(f"Source: {chunk['source']} | Type: {chunk['type']}")
            context_parts.append(chunk['content'])
            context_parts.append("")  # Empty line separator
        
        return "\n".join(context_parts)
    
    def get_syllabus_context(
        self,
        db: Session,
        course_id: int,
        week_number: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get syllabus context for a specific week.
        
        Args:
            db: Database session
            course_id: Course ID
            week_number: Week number
            
        Returns:
            Syllabus context dictionary or None
        """
        syllabus = (
            db.query(Syllabus)
            .filter(
                Syllabus.course_id == course_id,
                Syllabus.week_number == week_number,
                Syllabus.is_active == True
            )
            .first()
        )
        
        if not syllabus:
            return None
        
        return {
            "week_number": syllabus.week_number,
            "topic": syllabus.topic,
            "content": syllabus.content,
            "course_id": course_id
        }
    
    def _get_candidate_materials(
        self,
        db: Session,
        course_id: int,
        week_number: Optional[int] = None,
        approved_only: bool = True
    ) -> List[Material]:
        """
        Get candidate materials for retrieval.
        """
        # Start with MaterialTopic to filter by course/week
        query = (
            db.query(Material)
            .join(MaterialTopic, Material.id == MaterialTopic.material_id)
            .filter(MaterialTopic.course_id == course_id)
        )
        
        if week_number:
            query = query.filter(MaterialTopic.week_number == week_number)
        
        if approved_only:
            query = query.filter(MaterialTopic.approved_by_lecturer == True)
        
        return query.distinct().all()
    
    def _get_embedding(self, material: Material) -> List[float]:
        """
        Get or compute embedding for a material.
        """
        if material.embedding:
            return material.embedding
        
        # Compute embedding from content
        text_parts = [material.title or ""]
        if material.description:
            text_parts.append(material.description)
        if material.content_text:
            text_parts.append(material.content_text[:2000])
        
        return self.embedding_service.embed_text(" ".join(text_parts))
    
    def _extract_content(
        self,
        material: Material,
        query: str,
        max_length: int = 1000
    ) -> str:
        """
        Extract the most relevant content from a material.
        """
        # Prefer content_text if available
        if material.content_text:
            content = material.content_text
        elif material.description:
            content = material.description
        elif material.snippet:
            content = material.snippet
        else:
            content = material.title or ""
        
        # For now, simple truncation
        # TODO: Implement smarter extraction based on query relevance
        if len(content) > max_length:
            content = content[:max_length] + "..."
        
        return content


class ContextBuilder:
    """
    Helper class for building structured prompts with context.
    """
    
    SYSTEM_PROMPT_TEMPLATE = """You are an AI tutor for a university course. Your role is to:
1. Explain concepts clearly and accurately
2. Help students understand difficult topics
3. Provide hints and guidance without giving away full answers (unless in practice mode)
4. Use only the provided course materials as your knowledge base
5. Cite sources when referencing specific materials

Course: {course_name}
Current Topic: {topic}

{context}

Remember:
- Stay within the scope of the course materials
- Be encouraging and supportive
- Break down complex concepts into simpler parts
- Ask clarifying questions if the student's question is unclear
"""
    
    @classmethod
    def build_system_prompt(
        cls,
        course_name: str,
        topic: str,
        context: str
    ) -> str:
        """Build a system prompt with context."""
        return cls.SYSTEM_PROMPT_TEMPLATE.format(
            course_name=course_name,
            topic=topic,
            context=context
        )
