from typing import Any
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.embedding import ChunkEmbedding
from app.models.episode import Episode
from app.models.project import Project
from app.services.embedding_service import EmbeddingService, get_embedding_service

class SearchResultItem(BaseModel):
    episode_id: int
    episode_title: str
    project_id: int
    speaker: str
    text: str
    start_time: float
    end_time: float
    score: float

class SearchResponse(BaseModel):
    query: str
    total_results: int
    results: list[SearchResultItem]

class SemanticSearchService:
    def __init__(self, embedding_service: EmbeddingService | None = None):
        self.embedding_service = embedding_service or get_embedding_service()

    async def search(
        self,
        db: AsyncSession,
        query: str,
        project_id: int | None = None,
        episode_id: int | None = None,
        limit: int = 15,
        min_score: float = 0.0
    ) -> SearchResponse:
        """Executes vector similarity search using pgvector cosine distance against ChunkEmbedding."""
        query_vector = await self.embedding_service.get_embedding(query)

        # In pgvector, cosine distance is: ChunkEmbedding.embedding.cosine_distance(query_vector)
        # Cosine similarity score = 1 - cosine_distance
        cosine_distance = ChunkEmbedding.embedding.cosine_distance(query_vector)
        similarity_score = (1.0 - cosine_distance).label("similarity_score")

        stmt = (
            select(
                ChunkEmbedding.episode_id,
                Episode.title.label("episode_title"),
                Episode.project_id,
                ChunkEmbedding.speaker_label,
                ChunkEmbedding.chunk_text,
                ChunkEmbedding.start_time,
                ChunkEmbedding.end_time,
                similarity_score
            )
            .join(Episode, ChunkEmbedding.episode_id == Episode.id)
            .order_by(cosine_distance.asc())
            .limit(limit)
        )

        conditions = []
        if project_id is not None:
            conditions.append(Episode.project_id == project_id)
        if episode_id is not None:
            conditions.append(ChunkEmbedding.episode_id == episode_id)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        result = await db.execute(stmt)
        rows = result.all()

        results: list[SearchResultItem] = []
        for row in rows:
            # Format score between 0.0 and 1.0
            score = round(max(0.0, float(row.similarity_score)), 4)
            if score >= min_score:
                results.append(
                    SearchResultItem(
                        episode_id=row.episode_id,
                        episode_title=row.episode_title,
                        project_id=row.project_id,
                        speaker=row.speaker_label or "Speaker",
                        text=row.chunk_text,
                        start_time=row.start_time,
                        end_time=row.end_time,
                        score=score
                    )
                )

        return SearchResponse(
            query=query,
            total_results=len(results),
            results=results
        )


semantic_search_service = SemanticSearchService()
