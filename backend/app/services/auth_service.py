from typing import Optional
from datetime import timedelta
from app.database import get_database
from app.models.user import User
from app.utils.security import get_password_hash, verify_password, create_access_token
from app.utils.db_helpers import convert_objectid_to_str
from app.config import get_settings

settings = get_settings()


async def authenticate_or_create_user(
    username: str, password: str
) -> Optional[tuple[User, str]]:
    db = await get_database()
    user_dict = await db.users.find_one({"username": username})

    if user_dict:
        user_dict = convert_objectid_to_str(user_dict)
        user = User(**user_dict)

        if not verify_password(password, user.hashed_password):
            return None

        access_token = create_access_token(
            data={"sub": user.username},
            expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
        )
        return user, access_token
    else:
        hashed_password = get_password_hash(password)
        new_user = User(username=username, hashed_password=hashed_password)

        user_dict = new_user.model_dump(by_alias=True, exclude={"id"})
        result = await db.users.insert_one(user_dict)

        user_dict["_id"] = str(result.inserted_id)
        created_user = User(**user_dict)

        access_token = create_access_token(
            data={"sub": created_user.username},
            expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
        )
        return created_user, access_token


async def get_user_by_username(username: str) -> Optional[User]:
    db = await get_database()
    user_dict = await db.users.find_one({"username": username})

    if user_dict:
        user_dict = convert_objectid_to_str(user_dict)
        return User(**user_dict)
    return None
