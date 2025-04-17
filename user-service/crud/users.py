from crud.base_crud import RetrieveModelCRUD, CreateModelCRUD, LookupModelCRUD
from models import User
from schemas import UserInDBSchema


class UserCRUD(LookupModelCRUD):
	model = User
	lookup_field = "email"


class RetrieveUserCRUD(RetrieveModelCRUD,
					   UserCRUD):
	pass


class RetrieveCreateUserCRUD(RetrieveModelCRUD,
							 CreateModelCRUD[UserInDBSchema],
							 UserCRUD):
	pass

