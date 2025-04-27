from fastapi import APIRouter

email_router = APIRouter(prefix='/api/v1/email', tags=['email'])


@email_router.post("/send/")
async def send_email(to_email: str):
	subject = "Test Email"
	body = "This is a test email sent from FastAPI!"
	send_test_email(subject, body, to_email)
	return {"message": "Test email sent successfully"}