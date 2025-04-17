from crud.base_crud import RetrieveModelCRUD, CreateModelCRUD, UpdateModelCRUD
from models import User


class UserCRUD(RetrieveModelCRUD, CreateModelCRUD, UpdateModelCRUD):
	model = User
