# from crud.base_crud import ModelWithLookupCRUD, SingleModelCRUD
# from crud import mixins
# from models import User
# from schemas import UserInDBSchema
#
#
# class UserCRUD(ModelWithLookupCRUD,
# 			   SingleModelCRUD):
# 	model = User
# 	lookup_field = "email"
#
#
# class RetrieveUserCRUD(mixins.RetrieveModel,
# 					   UserCRUD):
# 	pass
#
#
# class RetrieveCreateUserCRUD(mixins.RetrieveModel,
# 							 mixins.CreateModel[UserInDBSchema],
# 							 UserCRUD):
# 	pass
#
