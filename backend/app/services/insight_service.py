import asyncio
from abc import ABC, abstractmethod
from pydantic import BaseModel

class InsightResult(BaseModel):
    overview: str
    target_competencies: list[dict]
    core_tech_stack: list[dict]
    architectural_blueprint: dict
    resume_transformation: list[dict]

class InsightService(ABC):
    @abstractmethod
    async def generate_insights(self, title: str, full_transcript: str) -> InsightResult:
        """Synthesizes structured architectural blueprint and competencies from podcast transcripts."""
        pass


class MockInsightService(InsightService):
    """Deterministic development AI Insight generator delivering comprehensive technical analyses."""
    async def generate_insights(self, title: str, full_transcript: str) -> InsightResult:
        await asyncio.sleep(0.4)
        
        return InsightResult(
            overview=(
                f"Deep-dive technical discussion on '{title}'. The session analyzes system design tradeoffs, "
                f"vector embedding indexing strategies with pgvector, and low-latency audio search pipeline architectures."
            ),
            target_competencies=[
                {
                    "title": "High-Concurrency Backend Architecture",
                    "level": "Expert",
                    "description": "Engineered non-blocking async ASGI pipelines with connection pooling and Redis caching."
                },
                {
                    "title": "Vector Databases & Semantic Retrieval",
                    "level": "Advanced",
                    "description": "Implemented pgvector indexing with cosine similarity distance and temporal window chunking."
                },
                {
                    "title": "Audio Diarization & Multimedia Processing",
                    "level": "Advanced",
                    "description": "Integrated speaker attribution and exact millisecond temporal alignment."
                },
                {
                    "title": "System Reliability & Idempotency",
                    "level": "Expert",
                    "description": "Guaranteed at-least-once execution and crash recovery with state machine workers."
                }
            ],
            core_tech_stack=[
                {"category": "Backend Engine", "technologies": ["FastAPI", "Python 3.11+", "Uvicorn", "AsyncIO"]},
                {"category": "Vector & Database", "technologies": ["PostgreSQL 16", "pgvector", "SQLAlchemy 2.0 Async", "Alembic"]},
                {"category": "AI & Processing", "technologies": ["Speaker Diarization", "Temporal Chunking", "Embedding Models"]},
                {"category": "Frontend & Streaming", "technologies": ["Next.js 15 App Router", "React 19", "HTML5 Audio Player", "Tailwind CSS"]}
            ],
            architectural_blueprint={
                "ingestion_flow": "Client Audio Upload -> Storage Abstraction -> Stage-by-Stage Async Pipeline",
                "retrieval_pipeline": "User Query -> Embedding Vector -> Cosine Distance Index Search -> Ranked Temporal Segments",
                "playback_deep_link": "Timestamped Segments -> HTML5 Player Seek -> Millisecond Accuracy Playback"
            },
            resume_transformation=[
                {
                    "bullet": "Architected an AI-powered podcast intelligence platform with sub-50ms semantic search using FastAPI, PostgreSQL, and pgvector.",
                    "impact": "Enabled instant cross-episode topic discovery with millisecond-accurate audio deep-linking."
                },
                {
                    "bullet": "Designed a speaker-aware temporal chunking engine that preserves conversational dialogue boundaries across multi-speaker episodes.",
                    "impact": "Boosted vector retrieval relevance by 45% compared to naive fixed-token windowing."
                },
                {
                    "bullet": "Constructed an asynchronous worker pipeline tracking multi-stage processing jobs with real-time UI state synchronization.",
                    "impact": "Eliminated HTTP request blocking and provided resilient crash recovery."
                }
            ]
        )


def get_insight_service() -> InsightService:
    return MockInsightService()
