from crud.base_crud import LookupModelCRUD, RetrieveModelCRUD, CreateModelCRUD


class TokenCRUD(LookupModelCRUD):
	model = 'BlacklistedToken'
	lookup_field = 'jti'


class RetrieveTokenCRUD(RetrieveModelCRUD,
						TokenCRUD):
	pass


class RetrieveCreateTokenCRUD(RetrieveModelCRUD,
							  CreateModelCRUD, # [ADD SCHEMA!]
							  TokenCRUD):
	pass
