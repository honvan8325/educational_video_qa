from fastapi import APIRouter, HTTPException, status
from app.schemas.user import LoginRequest, Token, UserResponse
from app.services.auth_service import authenticate_or_create_user
from fastapi import Depends
from app.api.deps import get_current_user

router = APIRouter()


@router.post("/login", response_model=Token)
async def login(request: LoginRequest):
    result = await authenticate_or_create_user(request.username, request.password)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    user, access_token = result

    return Token(access_token=access_token)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: UserResponse = Depends(get_current_user)):
    return current_user
