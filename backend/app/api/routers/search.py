from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.saved_search import SavedSearch
from app.schemas.search import (
    SearchRequest,
    SavedSearchCreate,
    SavedSearchUpdate,
    SavedSearchRead
)
from app.services.semantic_search_service import (
    semantic_search_service,
    SearchResponse
)

router = APIRouter(prefix="/search", tags=["Semantic Search"])

@router.post("", response_model=SearchResponse)
async def semantic_search(
    payload: SearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Executes pgvector semantic cosine similarity search across episode chunks."""
    return await semantic_search_service.search(
        db=db,
        query=payload.query,
        project_id=payload.project_id,
        episode_id=payload.episode_id,
        limit=payload.limit,
        min_score=payload.min_score
    )

@router.get("/saved", response_model=list[SavedSearchRead])
async def list_saved_searches(
    project_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = (
        select(SavedSearch)
        .where(SavedSearch.user_id == current_user.id)
        .order_by(SavedSearch.created_at.desc())
    )
    if project_id is not None:
        stmt = stmt.where(SavedSearch.project_id == project_id)
    
    res = await db.execute(stmt)
    return res.scalars().all()

@router.post("/saved", status_code=status.HTTP_201_CREATED, response_model=SavedSearchRead)
async def create_saved_search(
    payload: SavedSearchCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    saved_search = SavedSearch(
        user_id=current_user.id,
        project_id=payload.project_id,
        name=payload.name,
        query=payload.query,
        filters=payload.filters or {}
    )
    db.add(saved_search)
    await db.commit()
    await db.refresh(saved_search)
    return saved_search

@router.get("/saved/{id}", response_model=SavedSearchRead)
async def get_saved_search(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    saved_search = await db.get(SavedSearch, id)
    if not saved_search or saved_search.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Saved search not found")
    return saved_search

@router.patch("/saved/{id}", response_model=SavedSearchRead)
async def update_saved_search(
    id: int,
    payload: SavedSearchUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    saved_search = await db.get(SavedSearch, id)
    if not saved_search or saved_search.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Saved search not found")
    
    if payload.name is not None:
        saved_search.name = payload.name
    if payload.query is not None:
        saved_search.query = payload.query
    if payload.filters is not None:
        saved_search.filters = payload.filters
        
    await db.commit()
    await db.refresh(saved_search)
    return saved_search

@router.delete("/saved/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_saved_search(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    saved_search = await db.get(SavedSearch, id)
    if not saved_search or saved_search.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Saved search not found")
    
    await db.delete(saved_search)
    await db.commit()
    return None

@router.post("/saved/{id}/duplicate", status_code=status.HTTP_201_CREATED, response_model=SavedSearchRead)
async def duplicate_saved_search(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    original = await db.get(SavedSearch, id)
    if not original or original.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Saved search not found")
    
    dup = SavedSearch(
        user_id=current_user.id,
        project_id=original.project_id,
        name=f"{original.name} (Copy)",
        query=original.query,
        filters=original.filters
    )
    db.add(dup)
    await db.commit()
    await db.refresh(dup)
    return dup

@router.post("/saved/{id}/run", response_model=SearchResponse)
async def run_saved_search(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Executes a saved search using the exact same SemanticSearchService."""
    saved = await db.get(SavedSearch, id)
    if not saved or saved.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Saved search not found")
    
    filters = saved.filters or {}
    return await semantic_search_service.search(
        db=db,
        query=saved.query,
        project_id=saved.project_id or filters.get("project_id"),
        episode_id=filters.get("episode_id"),
        limit=filters.get("limit", 15),
        min_score=filters.get("min_score", 0.0)
    )
