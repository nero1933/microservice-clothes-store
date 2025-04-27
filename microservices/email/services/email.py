import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from starlette.exceptions import HTTPException


def send(subject: str, body: str, to_email: str):
	from_email = "nero.pet.1933@gmail.com"
	to_email = to_email

	msg = MIMEMultipart()
	msg['From'] = from_email
	msg['To'] = to_email
	msg['Subject'] = subject
	msg.attach(MIMEText(body, 'plain'))

	try:
		server = smtplib.SMTP('postfix', 587)
		server.sendmail(from_email, to_email, msg.as_string())
		server.quit()
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Error sending email: {str(e)}")
