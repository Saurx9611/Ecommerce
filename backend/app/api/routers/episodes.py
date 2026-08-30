import asyncio
import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.episode import Episode
from app.models.speaker import Speaker
from app.models.transcript import TranscriptSegment
from app.models.processing_job import ProcessingJob
from app.models.episode_insight import EpisodeInsight
from app.schemas.episode import (
    EpisodeRead,
    SpeakerRead,
    SpeakerUpdate,
    TranscriptSegmentRead,
    ProcessingJobRead,
    EpisodeInsightRead
)
from app.storage.storage_service import storage_service
from app.workers.pipeline_worker import pipeline_worker
from app.core.config import settings

router = APIRouter(prefix="/episodes", tags=["Episodes"])

@router.post("", status_code=status.HTTP_201_CREATED, response_model=EpisodeRead)
async def upload_episode(
    file: UploadFile = File(...),
    project_id: int = Form(...),
    title: str = Form(...),
    description: str | None = Form(None),
    language: str = Form("en"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify project ownership or existence
    project = await db.get(Project, project_id)
    if not project:
        # Create a default project if none exists for convenience
        project = Project(user_id=current_user.id, name="Default Podcast Project", description="Main workspace")
        db.add(project)
        await db.commit()
        await db.refresh(project)
        project_id = project.id

    # 1. Save audio to storage
    stored_meta = await storage_service.save_file(file, subfolder=f"proj_{project_id}")

    # 2. Create Episode Record
    episode = Episode(
        project_id=project_id,
        title=title,
        description=description,
        original_filename=stored_meta["filename"],
        audio_url=stored_meta["url"],
        file_size=stored_meta["file_size"],
        mime_type=stored_meta["mime_type"],
        language=language,
        status="queued"
    )
    db.add(episode)
    await db.commit()
    await db.refresh(episode, attribute_names=["speakers"])

    # 3. Create Processing Job
    job = ProcessingJob(
        episode_id=episode.id,
        status="queued",
        current_stage="upload",
        progress=0.0
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # 4. Trigger Async Processing Pipeline
    asyncio.create_task(pipeline_worker.process_episode(episode.id, job.id))

    return episode

@router.get("", response_model=list[EpisodeRead])
async def list_episodes(
    project_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = (
        select(Episode)
        .options(selectinload(Episode.speakers))
        .order_by(Episode.created_at.desc())
    )
    if project_id is not None:
        stmt = stmt.where(Episode.project_id == project_id)
    
    res = await db.execute(stmt)
    return res.scalars().all()

@router.get("/{id}", response_model=EpisodeRead)
async def get_episode(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = (
        select(Episode)
        .options(selectinload(Episode.speakers))
        .where(Episode.id == id)
    )
    res = await db.execute(stmt)
    episode = res.scalars().first()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    return episode

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_episode(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    episode = await db.get(Episode, id)
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    
    # Delete underlying audio file
    await storage_service.delete_file(episode.audio_url)
    
    await db.delete(episode)
    await db.commit()
    return None

@router.get("/{id}/transcript", response_model=list[TranscriptSegmentRead])
async def get_episode_transcript(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    episode = await db.get(Episode, id)
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    
    stmt = (
        select(TranscriptSegment)
        .options(selectinload(TranscriptSegment.speaker))
        .where(TranscriptSegment.episode_id == id)
        .order_by(TranscriptSegment.sequence_number.asc())
    )
    res = await db.execute(stmt)
    return res.scalars().all()

@router.get("/{id}/speakers", response_model=list[SpeakerRead])
async def get_episode_speakers(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Speaker).where(Speaker.episode_id == id).order_by(Speaker.id.asc())
    res = await db.execute(stmt)
    return res.scalars().all()

@router.patch("/{id}/speakers/{speaker_id}", response_model=SpeakerRead)
async def update_speaker(
    id: int,
    speaker_id: int,
    payload: SpeakerUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    speaker = await db.get(Speaker, speaker_id)
    if not speaker or speaker.episode_id != id:
        raise HTTPException(status_code=404, detail="Speaker not found on this episode")
    
    speaker.display_name = payload.display_name
    await db.commit()
    await db.refresh(speaker)
    return speaker

@router.get("/{id}/processing", response_model=ProcessingJobRead)
async def get_processing_status(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = (
        select(ProcessingJob)
        .where(ProcessingJob.episode_id == id)
        .order_by(ProcessingJob.started_at.desc())
    )
    res = await db.execute(stmt)
    job = res.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="No processing job found for this episode")
    return job

@router.post("/{id}/process", response_model=ProcessingJobRead)
async def trigger_episode_processing(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    episode = await db.get(Episode, id)
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    
    job = ProcessingJob(
        episode_id=episode.id,
        status="queued",
        current_stage="upload",
        progress=0.0
    )
    db.add(job)
    episode.status = "queued"
    await db.commit()
    await db.refresh(job)

    asyncio.create_task(pipeline_worker.process_episode(episode.id, job.id))
    return job

@router.get("/{id}/insights", response_model=EpisodeInsightRead)
async def get_episode_insights(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(EpisodeInsight).where(EpisodeInsight.episode_id == id)
    res = await db.execute(stmt)
    insight = res.scalars().first()
    if not insight:
        raise HTTPException(status_code=404, detail="Insights not generated yet for this episode")
    return insight

@router.get("/media/{file_path:path}")
async def serve_audio_media(file_path: str):
    """Streams the uploaded audio file for HTML5 player deep-linked playback."""
    abs_path = os.path.join(settings.UPLOAD_DIR, file_path)
    if not os.path.exists(abs_path):
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(abs_path)
