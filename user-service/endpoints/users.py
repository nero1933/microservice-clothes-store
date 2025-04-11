from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from models.users import User
from schemas import UserCreateSchema
from utils.user.create_user import create_user

router = APIRouter(prefix="/users", tags=["users"])


@router.post('/register', status_code=201)
async def register_user(user_data: UserCreateSchema, db: AsyncSession = Depends(get_db)):
    try:
        user = await create_user(db=db, user_data=user_data, is_active=True, is_admin=False)
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get('/all', status_code=201)
async def register_user(db: AsyncSession = Depends(get_db)):
    results = await db.execute(select(User))
    users = results.scalars().all()
    return {"users": users}
