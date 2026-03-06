"""Training recommendations endpoint."""
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.recommendations import RecommendationsResponse, TrainingRecommendation
from app.services.recommendations import get_recommendations as get_recommendations_service

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("", response_model=RecommendationsResponse)
async def recommendations(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> RecommendationsResponse:
    data = await get_recommendations_service(db, current_user.id)
    recs = [TrainingRecommendation(**r) for r in data["recommendations"]]
    return RecommendationsResponse(
        user_id=current_user.id,
        recommendations=recs,
        summary=data["summary"],
    )
