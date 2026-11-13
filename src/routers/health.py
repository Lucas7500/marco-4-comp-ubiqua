from fastapi import APIRouter

router: APIRouter = APIRouter()


@router.get("/health", response_model=None)
async def health() -> dict[str, str]:
    return {"status": "ok"}
