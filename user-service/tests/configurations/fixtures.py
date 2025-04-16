from http import cookies

import pytest_asyncio

from models import User
from utils import get_password_hash


@pytest_asyncio.fixture(loop_scope="function")
async def user_data():
	return {
		"email": "test@gmail.com",
		"password": "12345678",
		"first_name": "test",
		"last_name": "test",
	}


@pytest_asyncio.fixture(loop_scope="function")
async def user(session, user_data):
	user = User(
		email=user_data['email'],
		hashed_password=get_password_hash(user_data['password']),
		first_name="Test",
		last_name="User",
		is_active=True,
		is_admin=False
	)
	session.add(user)
	await session.commit()
	setattr(user, 'password', user_data['password'])
	return user


@pytest_asyncio.fixture(loop_scope="function")
async def auth_client(client, user):
	login_data = {
		"username": user.email,
		"password": user.password
	}
	login_response = await client.post("/api/v1/auth/login", data=login_data)
	assert login_response.status_code == 200

	access_token = login_response.json()["access_token"]
	refresh_token = login_response.cookies.get('refresh_token')

	client.headers.update({"Authorization": f"Bearer {access_token}"})
	setattr(client, 'refresh_token', refresh_token)
	yield client