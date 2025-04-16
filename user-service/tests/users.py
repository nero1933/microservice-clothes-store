import jwt
import pytest
from sqlalchemy import select

from core import settings
from models import User, BlacklistedToken
from utils import get_password_hash


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
async def test_register(client, user_data):
	response = await client.post("/api/v1/auth/register", json=user_data)
	assert response.status_code == 201


@pytest.mark.asyncio
async def test_register_duplicate_email(client, session, user_data):
	new_user = User(
		email=user_data['email'],
		hashed_password=get_password_hash(user_data['password']),
		first_name="Test",
		last_name="User",
		is_active=True,
		is_admin=False
	)
	session.add(new_user)
	await session.commit()

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

	response = await auth_client.post("/api/v1/auth/refresh")
	assert response.status_code == 200

	new_access_token = response.json().get('access_token')
	assert old_access_token != new_access_token

	new_refresh_token = response.cookies.get('refresh_token')
	assert old_refresh_token != new_refresh_token

	auth_client.headers.update({"Authorization": f"Bearer {new_access_token}"})
	response = await auth_client.get("/api/v1/auth/me")
	assert response.status_code == 200


@pytest.mark.asyncio
async def test_blacklist_token_when_refresh(auth_client, session):
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

	old_refresh_token_jti = jwt.decode(
		old_refresh_token,
		settings.JWT_TOKEN_SECRET_KEY,
		algorithms=[settings.JWT_TOKEN_ALGORITHM]
	).get('jti')

	stmt = select(BlacklistedToken).where(BlacklistedToken.jti == old_refresh_token_jti)
	result = await session.execute(stmt)
	token = result.scalar_one_or_none()
	assert token is not None

	response = await auth_client.post(
		"/api/v1/auth/refresh",
		cookies = {"refresh_token": new_refresh_token}
	)
	assert response.status_code == 200


@pytest.mark.asyncio
async def test_blacklist_token_when_logout(auth_client, session):
	old_access_token = auth_client.headers.get("Authorization").removeprefix("Bearer ").strip()
	old_refresh_token = auth_client.refresh_token

	response = await auth_client.post("/api/v1/auth/logout")
	assert response.status_code == 200

	response = await auth_client.get("/api/v1/auth/me")
	assert response.status_code == 401

	response = await auth_client.post(
		"/api/v1/auth/refresh",
		cookies = {"refresh_token": old_refresh_token}
	)
	assert response.status_code == 401

	old_access_token_jti = jwt.decode(
		old_access_token,
		settings.JWT_TOKEN_SECRET_KEY,
		algorithms=[settings.JWT_TOKEN_ALGORITHM]
	).get('jti')

	old_refresh_token_jti = jwt.decode(
		old_refresh_token,
		settings.JWT_TOKEN_SECRET_KEY,
		algorithms=[settings.JWT_TOKEN_ALGORITHM]
	).get('jti')

	stmt = select(BlacklistedToken) \
		.where(BlacklistedToken.jti.in_((old_access_token_jti, old_refresh_token_jti)))
	result = await session.execute(stmt)
	tokens = result.scalars().all()
	assert len(tokens) == 2
