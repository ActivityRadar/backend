# backend
Backend for the ActivityRadar platform.

## Setup

Run `pip install -r requirements.txt` in the project root after cloning and
setting up a virtual environment.

## Run

Run `uvicorn backend.main:app --reload` to start the server. Any saved changes
will make `uvicorn` reload the source files.

## Docs

See `127.0.0.1:8000/docs` for automatic and interactive API documentation.
