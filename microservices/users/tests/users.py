from asyncio import sleep

import pytest
from sqlalchemy import select

from models import User
from tests.configurations.conftest import test_prepare_database
from utils import password as p


@pytest.mark.asyncio
async def test_db_session(test_prepare_database):
	pass


@pytest.mark.asyncio
async def test_no_access_for_unauthenticated(client):
	no_access_for_unauthenticated: tuple[tuple[str, str], ...] = (
		('post', '/api/v1/auth/logout'),
		('get', '/api/v1/auth/me'),
	)

	for method, endpoint in no_access_for_unauthenticated:
		client_method = getattr(client, method)
		response = await client_method(endpoint)
		assert response.status_code == 401


@pytest.mark.asyncio
async def test_register(client, user_data, db):

	stmt = select(User)
	res = await db.execute(stmt)
	users = res.scalars().all()
	print(users)

	response = await client.post("/api/v1/auth/register", json=user_data)
	assert response.status_code == 201


@pytest.mark.asyncio
async def test_register_duplicate_email(client, db, user_data):
	new_user = User(
		email=user_data['email'],
		hashed_password=p.get_password_hash(user_data['password']),
		first_name="Test",
		last_name="User",
		is_active=True,
		is_admin=False
	)
	db.add(new_user)
	await db.commit()

	response = await client.post("/api/v1/auth/register", json=user_data)
	assert response.status_code == 400


@pytest.mark.asyncio
async def test_register_password(client, user_data):
	# Change password to unappropriated (less than 8 chars)
	user_data['password'] = '1234567'

	response = await client.post("/api/v1/auth/register", json=user_data)
	assert response.status_code == 422


@pytest.mark.asyncio
async def test_login(client, user):
	response = await client.post(
		"/api/v1/auth/login",
		data={ # 'data' for application/x-www-form-urlencoded
			"username": user.email,
			"password": user.password
		}
	)
	assert response.status_code == 200
	assert 'access_token' and 'token_type' in response.json()


@pytest.mark.asyncio
async def test_auth_with_refresh(auth_client):
	refresh_token = auth_client.refresh_token
	auth_client.headers["Authorization"] = f"Bearer {refresh_token}"

	response = await auth_client.get(
		"/api/v1/auth/me",
	)

	assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_self_user(auth_client):
	response = await auth_client.get("/api/v1/auth/me")
	assert response.status_code == 200
	assert any(x not in response.json() for x in ('id', 'password', 'hashed_password'))
	assert tuple(response.json().keys()) == (
		'email', 'first_name', 'last_name', 'is_active', 'created_at',
	)

@pytest.mark.asyncio
async def test_refresh(auth_client):
	old_access_token = auth_client.headers.get("Authorization").removeprefix("Bearer ").strip()
	old_refresh_token = auth_client.refresh_token

	await sleep(1) # Let token expire time change, otherwise access tokens will be the same
	response = await auth_client.post("/api/v1/auth/refresh")
	assert response.status_code == 200
	print(response.json())

	new_access_token = response.json().get('access_token')
	assert old_access_token != new_access_token

	new_refresh_token = response.cookies.get('refresh_token')
	assert old_refresh_token != new_refresh_token

	auth_client.headers.update({"Authorization": f"Bearer {new_access_token}"})
	response = await auth_client.get("/api/v1/auth/me")
	assert response.status_code == 200


@pytest.mark.asyncio
async def test_blacklist_token_when_refresh(auth_client):
	old_refresh_token = auth_client.refresh_token

	response = await auth_client.post("/api/v1/auth/refresh")
	assert response.status_code == 200

	new_access_token = response.json().get('access_token')
	new_refresh_token = response.cookies.get('refresh_token')

	auth_client.headers.update({"Authorization": f"Bearer {new_access_token}"})
	response = await auth_client.get("/api/v1/auth/me")
	assert response.status_code == 200

	response = await auth_client.post(
		"/api/v1/auth/refresh",
		cookies = {"refresh_token": old_refresh_token}
	)
	assert response.status_code == 401

	# old_refresh_token_jti = jwt.decode(
	# 	old_refresh_token,
	# 	settings.JWT_TOKEN_SECRET_KEY,
	# 	algorithms=[settings.JWT_TOKEN_ALGORITHM]
	# ).get('jti')
	#
	# response = await auth_client.post(
	# 	"/api/v1/auth/refresh",
	# 	cookies = {"refresh_token": new_refresh_token}
	# )
	# assert response.status_code == 200


@pytest.mark.asyncio
async def test_blacklist_token_when_logout(auth_client, db):
	old_refresh_token = auth_client.refresh_token

	response = await auth_client.post("/api/v1/auth/logout")
	assert response.status_code == 200

	response = await auth_client.post(
		"/api/v1/auth/refresh",
		cookies = {"refresh_token": old_refresh_token}
	)
	assert response.status_code == 401
