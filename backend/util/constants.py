import datetime
import os

import dotenv

dotenv.load_dotenv()


def get_env_or_throw(v):
    res = os.getenv(v)
    if res is None:
        raise Exception(f"Environment variable {v} not set!")

    print(f"ENVIRONMENT: {v}={res}")
    return res


MONGODB_CONNECTION_STRING = get_env_or_throw("MONGODB_CONNECTION_STRING")
DATABASE_NAME = get_env_or_throw("MONGO_DATABASE_NAME")
JWT_SECRET_KEY = get_env_or_throw("JWT_SECRET_KEY")
REFRESH_TOKEN_EXPIRY_TIME = datetime.timedelta(days=30)

DATE_FMT = "%Y-%m-%dT%H:%M:%SZ"


class Email:
    SMTP_SERVER = get_env_or_throw("MAIL_SERVER")
    SMTP_PORT = int(get_env_or_throw("MAIL_PORT"))
    SENDER_EMAIL = get_env_or_throw("MAIL_FROM")
    SENDER_PASSWORD = get_env_or_throw("MAIL_PASSWORD")
