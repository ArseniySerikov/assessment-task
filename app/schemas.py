from datetime import date, datetime
from pydantic import BaseModel, Field

class PlaceInput(BaseModel):
    external_id: int = Field(..., description="Artwork ID from Art Institute of Chicago API")

class PlaceUpdate(BaseModel):
    notes: str | None = Field(None, description="User notes for this place")
    is_visited: bool | None = Field(None, description="Mark place as visited")

class PlaceResponse(BaseModel):
    id: int
    project_id: int
    external_id: int
    title: str
    artist_display: str | None
    place_of_origin: str | None
    notes: str | None
    is_visited: bool
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


# Project 

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=2000)
    start_date: date | None = None
    places: list[PlaceInput] = Field(
        ...,
        min_length=1,
        max_length=10,
        description="List of places (1..10)",
    )

class ProjectUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=2000)
    start_date: date | None = None

class ProjectResponse(BaseModel):
    id: int
    name: str
    description: str | None
    start_date: date | None
    is_completed: bool
    created_at: datetime
    updated_at: datetime
    places: list[PlaceResponse] = []
    model_config = {"from_attributes": True}

class ProjectListResponse(BaseModel):
    id: int
    name: str
    description: str | None
    start_date: date | None
    is_completed: bool
    places_count: int
    visited_count: int
    created_at: datetime
    updated_at: datetime



class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    page_size: int
    total_pages: int