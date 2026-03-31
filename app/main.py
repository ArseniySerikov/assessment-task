from fastapi import FastAPI
from app.database import Base, engine
from app.routers import places, projects

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Traverl Planner API",
    description=(
        "A travel planning API that lets travellers create projects, "
        "collect places from the Art Institute of Chicago API"
    ),
    version="1.0.0",
)

app.include_router(projects.router, prefix="/api/v1")
app.include_router(places.router, prefix="/api/v1")

@app.get("/check", tags=["Health"])
def health_check():
    return {"ok": "ok"}
