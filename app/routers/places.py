from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from app.config import settings
from app.database import get_db
from app.models import Project, ProjectPlace
from app.schemas import PlaceInput, PlaceResponse, PlaceUpdate
from app.services.artic_api import ArticAPIError, validate_artwork_exists

router = APIRouter(
    prefix="/projects/{project_id}/places",
    tags=["Places"],
)

def _get_project_or_404(project_id: int, db: Session) -> Project:
    project = (
        db.query(Project)
        .options(joinedload(Project.places))
        .filter(Project.id == project_id)
        .first())
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def _check_and_update_completion(project: Project) -> None:
    if project.places and all(p.is_visited for p in project.places):
        project.is_completed = True
    else:
        project.is_completed = False


def _get_place_or_404(db: Session, project_id: int, place_id: int) -> ProjectPlace:
    place = (
        db.query(ProjectPlace)
        .filter(ProjectPlace.id == place_id, ProjectPlace.project_id == project_id)
        .first())
    if not place:
        raise HTTPException(status_code=404, detail="Place not found in this project")
    return place


@router.post("/", response_model=PlaceResponse, status_code=201)
async def add_place(
    project_id: int,
    payload: PlaceInput,
    db: Session = Depends(get_db),):
    project = _get_project_or_404(project_id, db)
    if len(project.places) >= settings.MAX_PLACES_PER_PROJECT: # enforce project limit: maximum 10 places.
        raise HTTPException(
            status_code=422,
            detail=f"Project already has the maximum of {settings.MAX_PLACES_PER_PROJECT} places",)

    existing = (
        db.query(ProjectPlace)
        .filter(
            ProjectPlace.project_id == project_id,
            ProjectPlace.external_id == payload.external_id,)
        .first())
    
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Place with external_id {payload.external_id} already exists in this project",)

    try:
        artwork = await validate_artwork_exists(payload.external_id)
    except ArticAPIError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    place = ProjectPlace(
        project_id=project_id,
        external_id=artwork.id,
        title=artwork.title,
        artist_display=artwork.artist_display,
        place_of_origin=artwork.place_of_origin,)
    db.add(place)

    _check_and_update_completion(project)
    db.commit()
    db.refresh(place)
    return place


@router.get("/", response_model=list[PlaceResponse])
def list_places(
    project_id: int,
    is_visited: bool | None = Query(None, description="Filter by visited status"),
    db: Session = Depends(get_db),):
    _get_project_or_404(project_id, db)

    query = db.query(ProjectPlace).filter(ProjectPlace.project_id == project_id)
    if is_visited is not None:
        query = query.filter(ProjectPlace.is_visited == is_visited)
    return query.order_by(ProjectPlace.created_at).all()


@router.get("/{place_id}", response_model=PlaceResponse)
def get_place(project_id: int, place_id: int, db: Session = Depends(get_db)):
    _get_project_or_404(project_id, db)
    return _get_place_or_404(db, project_id, place_id)


@router.patch("/{place_id}", response_model=PlaceResponse)
def update_place(
    project_id: int,
    place_id: int,
    payload: PlaceUpdate,
    db: Session = Depends(get_db),
):
    project = _get_project_or_404(project_id, db)
    place = _get_place_or_404(db, project_id, place_id)
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(place, field, value)
    _check_and_update_completion(project)

    db.commit()
    db.refresh(place)
    return place
