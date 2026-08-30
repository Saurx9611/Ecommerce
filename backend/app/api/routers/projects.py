from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.episode import Episode
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectRead

router = APIRouter(prefix="/projects", tags=["Projects"])

@router.get("", response_model=list[ProjectRead])
async def list_projects(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = (
        select(Project, func.count(Episode.id).label("episode_count"))
        .outerjoin(Episode, Project.id == Episode.project_id)
        .where(Project.user_id == current_user.id)
        .group_by(Project.id)
        .order_by(Project.created_at.desc())
    )
    res = await db.execute(stmt)
    rows = res.all()
    
    projects = []
    for proj, ep_count in rows:
        p_read = ProjectRead.model_validate(proj)
        p_read.episode_count = ep_count
        projects.append(p_read)
        
    return projects

@router.post("", status_code=status.HTTP_201_CREATED, response_model=ProjectRead)
async def create_project(
    payload: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = Project(
        user_id=current_user.id,
        name=payload.name,
        description=payload.description
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    p_read = ProjectRead.model_validate(project)
    p_read.episode_count = 0
    return p_read

@router.get("/{id}", response_model=ProjectRead)
async def get_project(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = await db.get(Project, id)
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get episode count
    res = await db.execute(select(func.count(Episode.id)).where(Episode.project_id == id))
    ep_count = res.scalar() or 0
    
    p_read = ProjectRead.model_validate(project)
    p_read.episode_count = ep_count
    return p_read

@router.patch("/{id}", response_model=ProjectRead)
async def update_project(
    id: int,
    payload: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = await db.get(Project, id)
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if payload.name is not None:
        project.name = payload.name
    if payload.description is not None:
        project.description = payload.description
        
    await db.commit()
    await db.refresh(project)
    return project

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = await db.get(Project, id)
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Project not found")
    
    await db.delete(project)
    await db.commit()
    return None
