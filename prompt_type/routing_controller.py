from fastapi import APIRouter

router = APIRouter(
    prefix="/api-v1/prompt-type",
    tags=["prompt-type"]
)

# Add your endpoints here