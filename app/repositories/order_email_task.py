from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from fastapi_mail import FastMail, MessageSchema, MessageType
import os
from dotenv import load_dotenv
from fastapi_mail import ConnectionConfig
from celery import Celery
import asyncio
load_dotenv()
app = Celery(
    'order_email_task',
    broker='redis://localhost:6379/0',
    include=['app.repositories.order_email_task']
)

conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv('MAIL_USERNAME'),
    MAIL_PASSWORD=os.getenv('MAIL_PASSWORD'),
    MAIL_FROM=os.getenv('MAIL_FROM'),
    MAIL_PORT=os.getenv('MAIL_PORT'),
    MAIL_SERVER=os.getenv('MAIL_SERVER'),
    MAIL_FROM_NAME=os.getenv('MAIL_FROM_NAME'),
    MAIL_STARTTLS=os.getenv('MAIL_STARTTLS')  ,
    MAIL_SSL_TLS=os.getenv('MAIL_SSL_TLS') ,
    USE_CREDENTIALS=os.getenv('USE_CREDENTIALS') ,
    VALIDATE_CERTS=os.getenv('VALIDATE_CERTS') ,
)



import tempfile
from fastapi_mail.errors import ConnectionErrors

@app.task
def create_pdf_and_send_email_task(email: str, items: list[dict]):
    # Create a temporary file to store the PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        c = canvas.Canvas(tmp.name, pagesize=letter)
        width, height = letter

        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, height - 50, "Order Receipt")

        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, height - 100, "Book ID")
        c.drawRightString(400, height - 100, "Quantity")
        c.drawRightString(500, height - 100, "Unit Price")
        c.drawRightString(600, height - 100, "Total")

        y = height - 130
        c.setFont("Helvetica", 11)
        total_cost = 0
        for item in items:
            c.drawString(50, y, str(item["book_id"]))
            c.drawRightString(400, y, str(item["quantity"]))
            c.drawRightString(500, y, f"{item['book_price']:.2f}")
            c.drawRightString(600, y, f"{item['items_total_price']:.2f}")
            total_cost += item["items_total_price"]
            y -= 20

        y -= 10
        c.setFont("Helvetica-Bold", 12)
        c.drawRightString(500, y, "Total:")
        c.drawRightString(600, y, f"{total_cost:.2f}")

        c.save()

    try:
        message = MessageSchema(
            subject="Your Order Receipt",
            recipients=[email],
            body="Thank you for your order. Please find your receipt attached.",
            subtype=MessageType.plain,
            attachments=[tmp.name]  # Pass path, not bytes
        )

        fm = FastMail(conf)
        asyncio.run(fm.send_message(message))

    except ConnectionErrors as e:
        print("Failed to send email:", str(e))

    finally:
        # Optional: clean up the temp file after sending
        os.unlink(tmp.name)
    