FROM python:3.10

WORKDIR /backend

# To show all python print statements in the logs
ENV PYTHONUNBUFFERED 1

# copy requirements and env file
COPY ./requirements.txt /backend/requirements.txt
COPY ./.env /backend/.env

RUN pip install --no-cache-dir --upgrade -r /backend/requirements.txt

COPY ./backend /backend/backend

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
