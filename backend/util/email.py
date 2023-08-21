import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate

from .constants import Email

smtp = None


# Connect to the SMTP server
def setup_email_server_connection():
    global smtp
    smtp = smtplib.SMTP_SSL(Email.SMTP_SERVER, Email.SMTP_PORT)
    smtp.ehlo()
    smtp.login(Email.SENDER_EMAIL, Email.SENDER_PASSWORD)


def create_body(username, code):
    return f"Hello {username}, this is your verification code for the ActivityRadar app: {code}"


def create_subject(code):
    return f"Your code: {code}"


async def send_verification_email(name: str, email_address: str, code: str):
    # Create a MIMEText object for the email content
    email_content = MIMEText(create_body(name, code), "plain")

    # Create a MIMEMultipart object to contain the email
    email = MIMEMultipart()
    email["From"] = f"ActivityRadar <{Email.SENDER_EMAIL}>"
    email["To"] = email_address
    email["Subject"] = create_subject(code)
    email["Date"] = formatdate(localtime=True)
    email.attach(email_content)

    try:
        smtp.sendmail(Email.SENDER_EMAIL, email_address, email.as_string())
    except Exception as e:
        print("Error sending email:", str(e))
