import os
from typing import List

from dotenv import load_dotenv
from fastapi import BackgroundTasks
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
 


load_dotenv()

conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv('MAIL_USERNAME'),
    MAIL_PASSWORD=os.getenv('MAIL_PASSWORD'),
    MAIL_FROM=os.getenv('MAIL_FROM'),
    MAIL_PORT=os.getenv('MAIL_PORT'),
    MAIL_SERVER=os.getenv('MAIL_SERVER'),
    MAIL_FROM_NAME=os.getenv('MAIL_FROM_NAME'),
    MAIL_STARTTLS=os.getenv('MAIL_STARTTLS'),
    MAIL_SSL_TLS=os.getenv('MAIL_SSL_TLS'),
    USE_CREDENTIALS=os.getenv('USE_CREDENTIALS'),
    VALIDATE_CERTS=os.getenv('VALIDATE_CERTS'),
)


async def send_in_background(
    email: List[str], background_tasks: BackgroundTasks, username: str
):
    message = MessageSchema(
        subject=f"Welcome {username} to our bookstore app.",
        recipients=email,
        body="On behalf of our team, we wish you a very nice day.",
        subtype=MessageType.plain,
    )

    fm = FastMail(conf)
    background_tasks.add_task(fm.send_message, message)  # Add email task to background

 