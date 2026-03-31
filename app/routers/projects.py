import math
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.models import Project, ProjectPlace
from app.schemas import (
    PaginatedResponse,
    ProjectCreate,
    ProjectListResponse,
    ProjectResponse,
    ProjectUpdate,
)
from app.services.artic_api import ArticAPIError, validate_artwork_exists

router = APIRouter(prefix="/projects", tags=["Projects"])


def _get_project_or_404(db: Session, project_id: int) -> Project:
    project = (
        db.query(Project)
        .options(joinedload(Project.places))
        .filter(Project.id == project_id)
        .first())
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def _validate_no_duplicates(external_ids: list[int]) -> None:
    if len(external_ids) != len(set(external_ids)):
        raise HTTPException(status_code=422, detail="Duplicate external_id in request")


def _build_project_list_item(db: Session, project: Project) -> ProjectListResponse:
    places_count = (
        db.query(func.count(ProjectPlace.id))
        .filter(ProjectPlace.project_id == project.id)
        .scalar())
    visited_count = (
        db.query(func.count(ProjectPlace.id))
        .filter(ProjectPlace.project_id == project.id, ProjectPlace.is_visited.is_(True))
        .scalar())
    return ProjectListResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        start_date=project.start_date,
        is_completed=project.is_completed,
        places_count=places_count,
        visited_count=visited_count,
        created_at=project.created_at,
        updated_at=project.updated_at,)


@router.post("/", response_model=ProjectResponse, status_code=201)
async def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    project = Project(
        name=payload.name,
        description=payload.description,
        start_date=payload.start_date,)
    # project must contain at least 1 place
    if not payload.places:
        raise HTTPException(
            status_code=422,
            detail="Project must contain at least 1 place",)
    external_ids = [place.external_id for place in payload.places]
    _validate_no_duplicates(external_ids)
    for place_in in payload.places:
        try:
            artwork = await validate_artwork_exists(place_in.external_id)
        except ArticAPIError as exc:
            raise HTTPException(status_code=422, detail=str(exc))
        project.places.append(
            ProjectPlace(
                external_id=artwork.id,
                title=artwork.title,
                artist_display=artwork.artist_display,
                place_of_origin=artwork.place_of_origin,))

    db.add(project)
    db.commit()
    db.refresh(project)
    return project

@router.get("/", response_model=PaginatedResponse)
def list_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_completed: bool | None = Query(None, description="Filter by completion status"),
    search: str | None = Query(None, description="Search by project name"),
    db: Session = Depends(get_db),):
    query = db.query(Project)

    if is_completed is not None:
        query = query.filter(Project.is_completed == is_completed)
    if search:
        query = query.filter(Project.name.ilike(f"%{search}%"))
    total = query.count()
    projects = (
        query.order_by(Project.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all())

    items = [_build_project_list_item(db, project) for project in projects]

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total else 0,)


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: int, db: Session = Depends(get_db)):
    return _get_project_or_404(db, project_id)


@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int, payload: ProjectUpdate, db: Session = Depends(get_db)):
    project = _get_project_or_404(db, project_id)
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)

    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: int, db: Session = Depends(get_db)):
    project = _get_project_or_404(db, project_id)

    if any(p.is_visited for p in project.places):
        raise HTTPException(
            status_code=409,
            detail="Cannot delete project with visited places",)

    db.delete(project)
    db.commit()