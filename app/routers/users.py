from __future__ import annotations

from fastapi import APIRouter

from app.core.deps import CurrentUser

router = APIRouter(prefix="/users/api", tags=["users"])


@router.get("/me")
async def get_my_profile(user: CurrentUser):
    return {"email": user.email, "is_active": user.is_active}


@router.get("/saved-applications")
async def list_saved_applications():
    return {
        "owner": "demo@example.com",
        "applications": [
            {
                "company": "ExampleCo",
                "role": "Senior Backend Engineer",
                "status": "draft",
            }
        ],
    }
