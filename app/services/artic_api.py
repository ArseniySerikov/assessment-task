from dataclasses import dataclass
import httpx
from cachetools import TTLCache
from app.config import settings

_cache: TTLCache = TTLCache(
    maxsize=settings.ARTIC_CACHE_MAX_SIZE,
    ttl=settings.ARTIC_CACHE_TTL # cache external API responses to reduce repeated network calls
)

@dataclass
class ArtworkInfo:
    id: int
    title: str
    artist_display: str | None
    place_of_origin: str | None


class ArticAPIError(Exception):
    pass


async def get_artwork(artwork_id: int) -> ArtworkInfo | None:
    cache_key = f"artwork:{artwork_id}"
    if cache_key in _cache:
        return _cache[cache_key]
    url = f"{settings.ARTIC_API_BASE_URL}/artworks/{artwork_id}"
    params = {"fields": "id,title,artist_display,place_of_origin"}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, params=params)
    except httpx.RequestError as exc:
        raise ArticAPIError(f"Failed to reach Art Institute API: {exc}") from exc
    if resp.status_code == 404:
        return None
    if resp.status_code != 200:
        raise ArticAPIError(
            f"Art Institute API returned status {resp.status_code}")
    data = resp.json().get("data")
    if not data:
        return None
    artwork = ArtworkInfo(
        id=data["id"],
        title=data.get("title", "Untitled"),
        artist_display=data.get("artist_display"),
        place_of_origin=data.get("place_of_origin"),)
    _cache[cache_key] = artwork
    return artwork


async def validate_artwork_exists(artwork_id: int) -> ArtworkInfo:
    artwork = await get_artwork(artwork_id)
    if artwork is None:
        raise ArticAPIError(
            f"Artwork with ID {artwork_id} not found in Art Institute API")
    return artwork

async def search_artworks(query: str, page: int = 1, limit: int = 10) -> dict:
    url = f"{settings.ARTIC_API_BASE_URL}/artworks/search"
    params = {
        "q": query,
        "fields": "id,title,artist_display,place_of_origin",
        "page": page,
        "limit": limit,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, params=params)
    except httpx.RequestError as exc:
        raise ArticAPIError(f"Failed to reach Art Institute API: {exc}") from exc

    if resp.status_code != 200:
        raise ArticAPIError(
            f"Art Institute API returned status {resp.status_code}")

    return resp.json()
