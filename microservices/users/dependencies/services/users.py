# from fastapi import Depends
# from sqlalchemy.ext.asyncio import AsyncSession
# from core.db import get_async_session
# from services.users import RegisterService, LoginService, UserMeService
#
#
# def get_register_service(
# 		db: AsyncSession = Depends(get_async_session),
# ) -> RegisterService:
# 	return RegisterService(db)
#
#
# def get_login_service(
# 		db: AsyncSession = Depends(get_async_session),
# ) -> LoginService:
# 	return LoginService(db)
#
#
# def get_user_me_service(
# 		db: AsyncSession = Depends(get_async_session),
# ) -> UserMeService:
# 	return UserMeService(db)
