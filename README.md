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

## For development

Run `pip install -r ./requirements-dev.txt` in your environment to install extra
development tools.
We are using [`pre-commit`](https://pre-commit.com/) for automatic code formatting.

Run `pre-commit install` to set up the hooks as pre-commit hooks.

Try it out by running `pre-commit run --all-files` from the project root.
