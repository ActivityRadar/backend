FROM python:3.11

WORKDIR /backend

# To show all python print statements in the logs
ENV PYTHONUNBUFFERED 1

# copy requirements and env file
COPY ./requirements.txt /backend/requirements.txt
COPY ./.env /backend/.env

RUN pip install --no-cache-dir --upgrade -r /backend/requirements.txt

# Uncomment this to save installed package versions
# inspect with `docker cp <container-name>:/backend/freeze.txt`
# RUN pip freeze > /backend/freeze.txt

COPY ./backend /backend/backend
